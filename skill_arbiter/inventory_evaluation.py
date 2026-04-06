from __future__ import annotations

import re
from pathlib import Path

from .threat_catalog import describe_codes
from supply_chain_guard import scan_skill_dir_content, scan_skill_tree, summarize_findings


def _read_skill_description(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ""
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"(?s)^---\n(.*?)\n---\n?", text)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _risk_from_codes(summary: dict[str, object]) -> tuple[str, list[str]]:
    findings = summary.get("findings", [])
    codes = list(dict.fromkeys(row["code"] for row in findings if isinstance(row, dict) and "code" in row))
    blocker_count = int(summary.get("blocker_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    if blocker_count:
        return "critical", codes
    if warning_count:
        return "high", codes
    return "low", codes


def _evaluate_skill_dir(skill_dir: Path, source_root: Path) -> tuple[str, list[str], list[dict[str, str]]]:
    content_summary = summarize_findings(scan_skill_dir_content(skill_dir))
    tree_summary = summarize_findings(scan_skill_tree(skill_dir, source_root))
    findings = list(content_summary["findings"]) + list(tree_summary["findings"])
    severity, codes = _risk_from_codes(
        {
            "blocker_count": int(content_summary["blocker_count"]) + int(tree_summary["blocker_count"]),
            "warning_count": int(content_summary["warning_count"]) + int(tree_summary["warning_count"]),
            "findings": findings,
        }
    )
    detail_by_code = {item["code"]: item for item in findings if isinstance(item, dict) and item.get("code")}
    details = []
    for descriptor in describe_codes(codes):
        message = ""
        finding = detail_by_code.get(descriptor["code"])
        if finding:
            message = str(finding.get("message") or "")
        details.append({**descriptor, "message": message})
    return severity, codes, details


def _coerce_evaluation(result: tuple[object, ...]) -> tuple[str, list[str], list[dict[str, str]]]:
    if len(result) == 3:
        severity, codes, details = result
        return str(severity), list(codes), list(details)
    severity, codes = result
    return str(severity), list(codes), describe_codes(list(codes))
