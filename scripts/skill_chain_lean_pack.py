#!/usr/bin/env python3
"""Generate lean chain workflows from full skill-chain audit output."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build lean chain pack from full chain audit JSON")
    parser.add_argument("--audit-json", required=True, help="Path to skill_chain_audit JSON output")
    parser.add_argument("--json-out", default="", help="Optional lean JSON output path")
    parser.add_argument("--md-out", default="", help="Optional lean Markdown output path")
    parser.add_argument(
        "--max-domain-skills",
        type=int,
        default=4,
        help="Maximum domain skills to include in lean execution steps per chain",
    )
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def unique(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        out.append(item)
        seen.add(item)
    return out


def build_lean_steps(chain: dict[str, object], max_domain_skills: int) -> list[str]:
    full_steps = [str(step) for step in chain.get("steps", [])]
    covered = [str(skill) for skill in chain.get("skills_covered", [])]

    preferred_core = [
        "skill-hub",
        "multitask-orchestrator",
        "manual-lane-split-fallback",
        "usage-watcher",
        "skill-cost-credit-governor",
        "skill-cold-start-warm-path-optimizer",
        "skills-cross-repo-radar",
        "code-gap-sweeping",
        "request-loopback-resume",
    ]
    tail = ["skill-auditor", "skill-enforcer"]

    core_steps = [step for step in preferred_core if step in full_steps]
    domain_steps = [skill for skill in covered if skill in full_steps][: max(max_domain_skills, 1)]
    tail_steps = [step for step in tail if step in full_steps]
    return unique(core_steps + domain_steps + tail_steps)


def build_lean_report(audit: dict[str, object], max_domain_skills: int) -> dict[str, object]:
    chains = audit.get("chain_workflows", [])
    if not isinstance(chains, list):
        raise ValueError("audit JSON missing chain_workflows")

    lean_rows: list[dict[str, object]] = []
    for chain in chains:
        if not isinstance(chain, dict):
            continue
        row = {
            "chain_id": chain.get("chain_id"),
            "title": chain.get("title"),
            "vendor": chain.get("vendor"),
            "intent": chain.get("intent"),
            "lean_steps": build_lean_steps(chain, max_domain_skills=max_domain_skills),
            "skills_covered_count": chain.get("skills_covered_count", 0),
            "skills_covered": chain.get("skills_covered", []),
        }
        lean_rows.append(row)

    summary = audit.get("summary", {})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_audit_generated_at": audit.get("generated_at"),
        "summary": {
            "activated_skill_count": summary.get("activated_skill_count"),
            "chain_count": len(lean_rows),
            "multitask_skill_present": summary.get("multitask_skill_present"),
            "multitask_step": summary.get("multitask_step"),
            "max_domain_skills_per_chain": max(max_domain_skills, 1),
        },
        "lean_chain_workflows": sorted(lean_rows, key=lambda item: str(item.get("chain_id"))),
    }


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    chains = report["lean_chain_workflows"]

    lines: list[str] = []
    lines.append("# Lean Activated Skill Chain Pack")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Source audit: `{report['source_audit_generated_at']}`")
    lines.append(f"- Activated skills: `{summary['activated_skill_count']}`")
    lines.append(f"- Chains: `{summary['chain_count']}`")
    lines.append(f"- Multitask skill present: `{summary['multitask_skill_present']}`")
    lines.append(f"- Multitask step: `{summary['multitask_step']}`")
    lines.append(f"- Max domain skills per chain: `{summary['max_domain_skills_per_chain']}`")
    lines.append("")
    lines.append("This pack is a compact execution profile. Use the full chain catalog for exhaustive lane detail.")
    lines.append("")

    for chain in chains:
        lines.append(f"## {chain['title']} (`{chain['chain_id']}`)")
        lines.append("")
        lines.append(f"- Vendor: `{chain['vendor']}`")
        lines.append(f"- Intent: {chain['intent']}")
        lines.append(f"- Covered skills: `{chain['skills_covered_count']}`")
        lines.append("- Lean steps:")
        for index, step in enumerate(chain["lean_steps"], start=1):
            lines.append(f"{index}. `{step}`")
        lines.append("- Skill options:")
        for skill in chain["skills_covered"]:
            lines.append(f"  - `{skill}`")
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
    audit_path = Path(args.audit_json).expanduser().resolve()
    if not audit_path.is_file():
        raise SystemExit(f"audit json not found: {audit_path}")

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    report = build_lean_report(audit, max_domain_skills=args.max_domain_skills)
    md = render_markdown(report)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        summary = report["summary"]
        print(f"activated_skills: {summary['activated_skill_count']}")
        print(f"chain_count: {summary['chain_count']}")
        print(f"multitask_skill_present: {summary['multitask_skill_present']}")
        print(f"multitask_step: {summary['multitask_step']}")
        print(f"max_domain_skills_per_chain: {summary['max_domain_skills_per_chain']}")

    write_json(args.json_out, report)
    write_text(args.md_out, md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

