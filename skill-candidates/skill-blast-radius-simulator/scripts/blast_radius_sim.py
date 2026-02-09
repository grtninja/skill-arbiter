#!/usr/bin/env python3
"""Simulate skill blast radius before enabling/installing it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

DESTRUCTIVE_PATTERNS = (
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+checkout\s+--\b",
    r"\brm\s+-rf\b",
    r"\bdel\s+/f\b",
    r"\bformat\s+[a-z]:",
)

NETWORK_PATTERNS = (
    r"\bcurl\b",
    r"\bwget\b",
    r"https?://",
)

WRITE_PATTERNS = (
    r"write_text\(",
    r"\.write\(",
    r"open\([^\n]+['\"]w['\"]",
)

ABSOLUTE_PATH_PATTERNS = (
    r"/home/",
    r"/Users/",
    r"C:\\\\Users\\\\",
)

RG_PATTERN = re.compile(r"\brg\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate blast radius risk for skill candidates")
    parser.add_argument("--skills-root", default="skill-candidates", help="Skill root directory")
    parser.add_argument("--skill", action="append", default=[], help="Skill name to simulate (repeatable)")
    parser.add_argument("--baseline-json", default="", help="Optional prior simulation JSON for delta comparison")
    parser.add_argument(
        "--ack-threshold",
        choices=("low", "medium", "high", "critical"),
        default="high",
        help="Require explicit acknowledgement at or above this risk level",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def risk_rank(level: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(level, 0)


def classify_risk(score: int) -> str:
    if score >= 10:
        return "critical"
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def count_pattern_hits(text: str, patterns: tuple[str, ...]) -> int:
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, flags=re.IGNORECASE))
    return count


def find_skill_dirs(root: Path, names: set[str]) -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        if names and child.name not in names:
            continue
        if (child / "SKILL.md").is_file():
            skills[child.name] = child
    return skills


def read_baseline(path_text: str) -> dict[str, int]:
    if not path_text:
        return {}
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"baseline file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline JSON must be an object")

    rows = payload.get("skills")
    if not isinstance(rows, list):
        return {}

    values: dict[str, int] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill") or "").strip()
        score = item.get("risk_score")
        if not skill:
            continue
        try:
            values[skill] = int(score)
        except (TypeError, ValueError):
            continue
    return values


def simulate_skill(skill: str, path: Path) -> dict[str, Any]:
    markdown = (path / "SKILL.md").read_text(encoding="utf-8")
    script_paths = sorted(path.rglob("*.py"))

    script_texts: list[str] = []
    script_loc = 0
    for script in script_paths:
        text = script.read_text(encoding="utf-8")
        script_texts.append(text)
        script_loc += len(text.splitlines())

    combined = "\n\n".join([markdown] + script_texts)

    destructive_hits = count_pattern_hits(combined, DESTRUCTIVE_PATTERNS)
    network_hits = count_pattern_hits(combined, NETWORK_PATTERNS)
    absolute_hits = count_pattern_hits(combined, ABSOLUTE_PATH_PATTERNS)
    shell_true_hits = len(re.findall(r"shell\s*=\s*True", combined))
    os_system_hits = len(re.findall(r"os\.system\(", combined))
    write_hits = count_pattern_hits(combined, WRITE_PATTERNS)

    rg_hits = len(RG_PATTERN.findall(combined))
    bounded_index_hits = len(re.findall(r"safe-mass-index-core|--max-seconds|--max-files-per-run", combined))

    score = 0
    score += destructive_hits * 5
    score += shell_true_hits * 3
    score += os_system_hits * 3
    score += network_hits * 2
    score += absolute_hits * 2
    score += 1 if rg_hits > 0 else 0
    score += 1 if write_hits > 0 else 0
    score += 2 if rg_hits > 0 and bounded_index_hits == 0 else 0
    score += 1 if script_loc > 600 else 0
    score += 1 if len(script_paths) > 6 else 0
    score = int(score)

    risk_level = classify_risk(score)

    index_scope = "narrow"
    if rg_hits > 0 and bounded_index_hits == 0:
        index_scope = "broad"
    elif rg_hits > 0 or bounded_index_hits > 0:
        index_scope = "bounded"

    filesystem_reach = "local"
    if absolute_hits > 0:
        filesystem_reach = "extended"
    elif write_hits > 0:
        filesystem_reach = "repo-write"

    token_risk = "low"
    if "loop" in markdown.lower() or "retry" in markdown.lower() or "fan-out" in markdown.lower():
        token_risk = "medium"
    if network_hits > 0 and ("agent" in markdown.lower() or "bridge" in markdown.lower()):
        token_risk = "high"

    cpu_risk = "low"
    if index_scope == "broad":
        cpu_risk = "high"
    elif index_scope == "bounded":
        cpu_risk = "medium"

    reasons: list[str] = []
    if destructive_hits > 0:
        reasons.append("destructive_command_pattern")
    if shell_true_hits > 0 or os_system_hits > 0:
        reasons.append("unsafe_shell_invocation")
    if network_hits > 0:
        reasons.append("network_activity_detected")
    if absolute_hits > 0:
        reasons.append("absolute_path_detected")
    if rg_hits > 0:
        reasons.append("repo_scan_command_detected")
    if rg_hits > 0 and bounded_index_hits == 0:
        reasons.append("unbounded_scan_risk")
    if write_hits > 0:
        reasons.append("file_mutation_detected")

    return {
        "skill": skill,
        "risk_score": score,
        "risk_level": risk_level,
        "signals": {
            "destructive_hits": destructive_hits,
            "shell_true_hits": shell_true_hits,
            "os_system_hits": os_system_hits,
            "network_hits": network_hits,
            "absolute_path_hits": absolute_hits,
            "rg_hits": rg_hits,
            "bounded_index_hits": bounded_index_hits,
            "write_hits": write_hits,
            "script_count": len(script_paths),
            "script_loc": script_loc,
        },
        "predicted_impact": {
            "index_scope": index_scope,
            "filesystem_reach": filesystem_reach,
            "token_risk": token_risk,
            "cpu_risk": cpu_risk,
        },
        "reason_codes": sorted(set(reasons)),
    }


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def render_table(report: dict[str, Any]) -> str:
    lines = [
        f"skills_root: {report['skills_root']}",
        f"ack_threshold: {report['ack_threshold']}",
        "",
        "skill                              risk       score  ack_required  index_scope  cpu_risk",
        "---------------------------------  ---------  -----  ------------  -----------  --------",
    ]

    for row in report["skills"]:
        lines.append(
            "{skill:<33}  {level:<9}  {score:>5}  {ack:<12}  {scope:<11}  {cpu:<8}".format(
                skill=row["skill"][:33],
                level=row["risk_level"],
                score=int(row["risk_score"]),
                ack=str(row["ack_required"]),
                scope=row["predicted_impact"]["index_scope"],
                cpu=row["predicted_impact"]["cpu_risk"],
            )
        )

    lines.append("")
    lines.append("recommendations:")
    for item in report["recommendations"]:
        lines.append(f"- {item}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.is_dir():
        raise FileNotFoundError(f"skills root not found: {skills_root}")

    selected = {str(item).strip() for item in args.skill if str(item).strip()}
    skills = find_skill_dirs(skills_root, selected)
    if not skills:
        raise ValueError("no matching skills found")

    baseline = read_baseline(args.baseline_json)
    threshold_rank = risk_rank(str(args.ack_threshold))

    rows = []
    for skill, path in skills.items():
        row = simulate_skill(skill, path)
        baseline_score = baseline.get(skill)
        if baseline_score is not None:
            row["baseline_score"] = int(baseline_score)
            row["risk_delta"] = int(row["risk_score"]) - int(baseline_score)
        else:
            row["baseline_score"] = None
            row["risk_delta"] = None

        ack_required = risk_rank(str(row["risk_level"])) >= threshold_rank
        if row["risk_delta"] is not None and int(row["risk_delta"]) >= 3:
            ack_required = True
        row["ack_required"] = bool(ack_required)
        rows.append(row)

    rows.sort(key=lambda item: (-int(item["risk_score"]), item["skill"]))

    recommendations: list[str] = []
    if any(item["ack_required"] for item in rows):
        recommendations.append("Require explicit acknowledgement for flagged skills before install/enable.")
    if any(item["predicted_impact"]["index_scope"] == "broad" for item in rows):
        recommendations.append("Constrain scans with bounded index budgets before rollout.")
    if any("unsafe_shell_invocation" in item["reason_codes"] for item in rows):
        recommendations.append("Replace shell-string execution with argument-safe subprocess calls.")
    if not recommendations:
        recommendations.append("No high-risk signals detected under current heuristics.")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skills_root": str(skills_root),
        "ack_threshold": str(args.ack_threshold),
        "skills": rows,
        "recommendations": recommendations,
    }

    write_json(args.json_out, report)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(render_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
