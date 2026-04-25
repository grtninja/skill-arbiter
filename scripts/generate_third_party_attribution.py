#!/usr/bin/env python3
"""Generate third-party attribution manifest/docs for imported skills."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess


RENAME_MAP = {"skill-creator": "skill-creator-openclaw"}


def alias_source_root(label: str, path: Path) -> str:
    normalized = str(path).replace("\\", "/")
    if "openclaw" in normalized and "extensions" in normalized:
        return "<THIRD_PARTY_CLONES>/openclaw/extensions"
    if "openclaw" in normalized:
        return "<THIRD_PARTY_CLONES>/openclaw/skills"
    if "nullclaw" in normalized:
        return "<THIRD_PARTY_CLONES>/nullclaw"
    return f"<THIRD_PARTY_CLONES>/{label}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate third-party skill attribution outputs")
    parser.add_argument(
        "--intake-json",
        required=True,
        help="Path to third-party intake JSON artifact",
    )
    parser.add_argument(
        "--skills-root",
        required=True,
        help="Path to repository skill-candidates root",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON attribution output")
    parser.add_argument("--md-out", default="", help="Optional Markdown attribution output")
    return parser.parse_args()


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def find_repo_root(path: Path) -> Path | None:
    current = path
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def detect_license(repo: Path) -> str:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
        path = repo / name
        if path.is_file():
            return name
    return ""


def parse_source_roots(intake: dict[str, object]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for raw in intake.get("sources", []):
        if not isinstance(raw, str) or "=" not in raw:
            continue
        label, value = raw.split("=", 1)
        roots[label.strip()] = Path(value.strip())
    return roots


def build_attribution(intake: dict[str, object], skills_root: Path) -> dict[str, object]:
    source_roots = parse_source_roots(intake)
    source_meta: dict[str, dict[str, object]] = {}

    for label, root in source_roots.items():
        repo_root = find_repo_root(root)
        if repo_root is None:
            source_meta[label] = {
                "label": label,
                "source_root": alias_source_root(label, root),
                "repo_root": None,
                "git_commit": "",
                "remote_url": "",
                "license_file": "",
            }
            continue
        source_meta[label] = {
            "label": label,
            "source_root": alias_source_root(label, root),
            "repo_root": f"<THIRD_PARTY_CLONES>/{repo_root.name}",
            "git_commit": run_git(repo_root, ["rev-parse", "HEAD"]),
            "remote_url": run_git(repo_root, ["remote", "get-url", "origin"]),
            "license_file": detect_license(repo_root),
        }

    rows: list[dict[str, object]] = []
    for item in intake.get("skills", []):
        if not isinstance(item, dict):
            continue
        origin_name = str(item.get("skill", "")).strip()
        if not origin_name:
            continue
        target_name = RENAME_MAP.get(origin_name, origin_name)
        target_path = skills_root / target_name
        if not target_path.is_dir():
            # only attribute skills actually present in this repository
            continue
        source_label = str(item.get("source", "")).strip()
        source = source_meta.get(source_label, {})
        source_root_path = source_roots.get(source_label)
        origin_path_abs = Path(str(item.get("path", "")))
        origin_path = str(origin_path_abs).replace("\\", "/")
        if source_root_path is not None:
            try:
                rel = origin_path_abs.relative_to(source_root_path)
                rel_text = str(rel).replace("\\", "/")
                origin_path = f"{source.get('source_root', source_label)}/{rel_text}"
            except ValueError:
                origin_path = f"{source.get('source_root', source_label)}/{origin_name}"
        rows.append(
            {
                "skill": target_name,
                "origin_skill": origin_name,
                "source_label": source_label,
                "recommendation": item.get("recommendation", ""),
                "origin_path": origin_path,
                "source_root": source.get("source_root", ""),
                "repo_root": source.get("repo_root", ""),
                "git_commit": source.get("git_commit", ""),
                "remote_url": source.get("remote_url", ""),
                "license_file": source.get("license_file", ""),
            }
        )

    rows.sort(key=lambda row: str(row["skill"]).lower())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skills_root": str(skills_root),
        "third_party_skill_count": len(rows),
        "sources": list(source_meta.values()),
        "skills": rows,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Third-Party Skill Attribution")
    lines.append("")
    lines.append("This document attributes all third-party-origin skills currently included in `skill-candidates/`.")
    lines.append("")
    lines.append(f"- Generated: `{payload['generated_at']}`")
    lines.append(f"- Attributed skills: `{payload['third_party_skill_count']}`")
    lines.append("")
    lines.append("## Source Repositories")
    lines.append("")
    lines.append("| Label | Source Root | Repo Root | Commit | Remote | License |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for source in payload["sources"]:
        lines.append(
            "| `{label}` | `{source_root}` | `{repo_root}` | `{git_commit}` | `{remote_url}` | `{license_file}` |".format(
                label=source.get("label", ""),
                source_root=source.get("source_root", ""),
                repo_root=source.get("repo_root", ""),
                git_commit=source.get("git_commit", ""),
                remote_url=source.get("remote_url", ""),
                license_file=source.get("license_file", ""),
            )
        )
    lines.append("")
    lines.append("## Skill Attribution Matrix")
    lines.append("")
    lines.append("| Skill (local) | Origin Skill | Source | Intake Recommendation | Origin Path |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in payload["skills"]:
        lines.append(
            "| `{skill}` | `{origin_skill}` | `{source_label}` | `{recommendation}` | `{origin_path}` |".format(
                skill=row.get("skill", ""),
                origin_skill=row.get("origin_skill", ""),
                source_label=row.get("source_label", ""),
                recommendation=row.get("recommendation", ""),
                origin_path=row.get("origin_path", ""),
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_json(path_text: str, payload: dict[str, object]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path_text: str, content: str) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    intake_path = Path(args.intake_json).expanduser().resolve()
    skills_root = Path(args.skills_root).expanduser().resolve()
    if not intake_path.is_file():
        raise SystemExit(f"intake JSON not found: {intake_path}")
    if not skills_root.is_dir():
        raise SystemExit(f"skills root not found: {skills_root}")

    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    payload = build_attribution(intake, skills_root=skills_root)
    md = render_markdown(payload)

    print(f"third_party_skill_count: {payload['third_party_skill_count']}")
    for source in payload["sources"]:
        print(
            f"- {source.get('label')}: commit={source.get('git_commit')} license={source.get('license_file') or 'n/a'}"
        )

    write_json(args.json_out, payload)
    write_text(args.md_out, md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
