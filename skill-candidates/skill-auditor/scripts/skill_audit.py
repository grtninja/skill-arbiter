#!/usr/bin/env python3
"""Audit skill candidates and classify each target skill as unique or upgrade."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

STOPWORDS = {
    "the",
    "and",
    "to",
    "of",
    "in",
    "for",
    "with",
    "or",
    "a",
    "an",
    "is",
    "are",
    "use",
    "when",
    "this",
    "skill",
    "that",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and classify skill candidates")
    parser.add_argument("--skills-root", default="skill-candidates", help="Skill candidates root")
    parser.add_argument("--include-skill", action="append", default=[], help="Skill name to audit (repeatable)")
    parser.add_argument("--exclude-skill", action="append", default=[], help="Skill name to exclude (repeatable)")
    parser.add_argument(
        "--upgrade-threshold",
        type=float,
        default=0.26,
        help="Similarity threshold for upgrade classification",
    )
    parser.add_argument("--arbiter-report", default="", help="Optional skill-arbiter JSON report path")
    parser.add_argument(
        "--require-arbiter-evidence",
        action="store_true",
        help="Fail with high finding when arbiter evidence for a target skill is missing",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def normalize_name(name: str) -> str:
    return str(name or "").strip()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text
    end_index = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index < 0:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")
    body = "\n".join(lines[end_index + 1 :])
    return metadata, body


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9-_/]{1,}", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_skill_docs(skills_root: Path) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    for child in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        metadata, body = parse_frontmatter(text)
        docs[child.name] = {
            "skill": child.name,
            "path": str(skill_md),
            "metadata": metadata,
            "line_count": len(text.splitlines()),
            "tokens": tokenize(body),
            "agents_openai_yaml": (child / "agents" / "openai.yaml").is_file(),
        }
    return docs


def parse_arbiter_results(path_text: str) -> dict[str, dict[str, Any]]:
    if not path_text:
        return {}
    path = Path(path_text).expanduser().resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"arbiter report root must be object: {path}")
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise ValueError(f"arbiter report missing results list: {path}")

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        skill = normalize_name(str(row.get("skill") or ""))
        if not skill:
            continue
        raw_max = row.get("max_rg")
        max_rg: int | None
        try:
            max_rg = int(raw_max)
        except (TypeError, ValueError):
            max_rg = None
        out[skill] = {
            "action": normalize_name(str(row.get("action") or "")).lower(),
            "persistent_nonzero": bool(row.get("persistent_nonzero")),
            "max_rg": max_rg,
        }
    return out


def nearest_peer(
    skill: str,
    docs: dict[str, dict[str, Any]],
) -> tuple[str, float]:
    if skill not in docs:
        return "", 0.0
    current = docs[skill]
    best_peer = ""
    best_score = 0.0
    for other_skill, other_doc in docs.items():
        if other_skill == skill:
            continue
        score = jaccard(current["tokens"], other_doc["tokens"])
        if score > best_score:
            best_score = score
            best_peer = other_skill
    return best_peer, best_score


def add_finding(
    findings: list[dict[str, Any]],
    *,
    skill: str,
    severity: str,
    code: str,
    message: str,
) -> None:
    findings.append(
        {
            "skill": skill,
            "severity": severity,
            "code": code,
            "message": message,
        }
    )


def render_table(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"skills_root: {payload['skills_root']}")
    lines.append(f"skills_scanned: {payload['skills_scanned']}")
    lines.append("")
    lines.append("classifications:")
    for row in payload["classifications"]:
        peer = row["nearest_peer"] if row["nearest_peer"] else "-"
        lines.append(
            f"- {row['skill']}: {row['classification']} nearest={peer} similarity={row['similarity']:.3f}"
        )
    lines.append("")
    lines.append("findings:")
    if payload["findings"]:
        for row in payload["findings"]:
            lines.append(f"- [{row['severity']}] {row['skill']} {row['code']}: {row['message']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append(
        "counts: high={high} medium={medium} low={low}".format(
            high=payload["high_count"],
            medium=payload["medium_count"],
            low=payload["low_count"],
        )
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.is_dir():
        print(f"error: skills root not found: {skills_root}", file=sys.stderr)
        return 2

    try:
        docs = load_skill_docs(skills_root)
        arbiter = parse_arbiter_results(args.arbiter_report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    include = {normalize_name(item) for item in args.include_skill if normalize_name(item)}
    exclude = {normalize_name(item) for item in args.exclude_skill if normalize_name(item)}

    if include:
        missing = sorted(name for name in include if name not in docs)
        if missing:
            print(f"error: include-skill not found: {', '.join(missing)}", file=sys.stderr)
            return 2
        targets = sorted(name for name in include if name not in exclude)
    else:
        targets = sorted(name for name in docs.keys() if name not in exclude)

    findings: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []

    threshold = float(args.upgrade_threshold)
    for skill in targets:
        doc = docs[skill]
        metadata = doc["metadata"]
        metadata_name = normalize_name(metadata.get("name", ""))
        metadata_description = normalize_name(metadata.get("description", ""))

        peer, similarity = nearest_peer(skill, docs)
        classification = "upgrade" if similarity >= threshold else "unique"

        classifications.append(
            {
                "skill": skill,
                "classification": classification,
                "nearest_peer": peer,
                "similarity": round(similarity, 4),
            }
        )

        if not metadata_name or not metadata_description:
            add_finding(
                findings,
                skill=skill,
                severity="high",
                code="frontmatter_missing",
                message="SKILL.md must define name and description in frontmatter.",
            )
        if metadata_name and metadata_name != skill:
            add_finding(
                findings,
                skill=skill,
                severity="medium",
                code="frontmatter_name_mismatch",
                message=f"frontmatter name={metadata_name!r} does not match folder name {skill!r}.",
            )
        if not bool(doc["agents_openai_yaml"]):
            add_finding(
                findings,
                skill=skill,
                severity="medium",
                code="agents_openai_missing",
                message="agents/openai.yaml is missing.",
            )
        if int(doc["line_count"]) > 500:
            add_finding(
                findings,
                skill=skill,
                severity="low",
                code="skill_md_large",
                message=f"SKILL.md has {doc['line_count']} lines; consider splitting references.",
            )
        if classification == "upgrade" and similarity >= 0.45:
            add_finding(
                findings,
                skill=skill,
                severity="low",
                code="high_overlap",
                message=f"overlap with {peer!r} is high ({similarity:.3f}); tighten boundaries.",
            )

        arbiter_row = arbiter.get(skill)
        if args.require_arbiter_evidence and arbiter_row is None:
            add_finding(
                findings,
                skill=skill,
                severity="high",
                code="arbiter_missing",
                message="required arbiter evidence is missing for this skill.",
            )
        if arbiter_row is not None:
            action = str(arbiter_row.get("action") or "")
            persistent = bool(arbiter_row.get("persistent_nonzero"))
            max_rg = arbiter_row.get("max_rg")
            invalid_arbiter = action != "kept" or persistent or not isinstance(max_rg, int) or max_rg > 3
            if invalid_arbiter:
                severity = "high" if args.require_arbiter_evidence else "medium"
                add_finding(
                    findings,
                    skill=skill,
                    severity=severity,
                    code="arbiter_failed",
                    message=(
                        "arbiter evidence must be action=kept, persistent_nonzero=false, "
                        "and max_rg<=3."
                    ),
                )

    classifications.sort(key=lambda item: item["skill"])
    findings.sort(key=lambda item: (item["severity"], item["skill"], item["code"]))

    high_count = sum(1 for item in findings if item["severity"] == "high")
    medium_count = sum(1 for item in findings if item["severity"] == "medium")
    low_count = sum(1 for item in findings if item["severity"] == "low")

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skills_root": str(skills_root),
        "skills_scanned": len(targets),
        "include_skills": sorted(include),
        "exclude_skills": sorted(exclude),
        "upgrade_threshold": threshold,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "classifications": classifications,
        "findings": findings,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(render_table(payload))

    write_json(args.json_out, payload)
    if high_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
