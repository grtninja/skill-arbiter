#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.inventory import build_inventory_snapshot
from skill_arbiter.paths import REPO_ROOT


def _section(lines: list[str], title: str, rows: list[dict[str, object]]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not rows:
        lines.append("_None._")
        return
    lines.extend(
        [
            "| Skill | Ownership | Legitimacy | Risk | Action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| `{name}` | `{ownership}` | `{legitimacy_status}` | `{risk_class}` | `{recommended_action}` |".format(
                **row
            )
        )


def render_report(payload: dict[str, object]) -> str:
    skills = list(payload.get("skills", []))
    legitimacy = payload.get("legitimacy_summary", {})
    review_rows = [row for row in skills if row.get("legitimacy_status") in {"official_review", "owned_review", "baseline_review", "manual_review"}]
    lines = [
        "# NullClaw Skill Vetting Report",
        "",
        "This document is machine-generated from the live inventory model and is safe for public publication.",
        "",
        "## Summary",
        "",
        f"- Generated: `{payload.get('generated_at', '')}`",
        "- Host ID: `<LOCAL_HOST_ID>`",
        f"- Official trusted: `{legitimacy.get('official_trusted', 0)}`",
        f"- Owned trusted: `{legitimacy.get('owned_trusted', 0)}`",
        f"- Needs review: `{legitimacy.get('needs_review', 0)}`",
        f"- Blocked hostile: `{legitimacy.get('blocked_hostile', 0)}`",
        "",
        "## Interop surfaces",
        "",
        "| Surface | Scope | Presence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload.get("interop_sources", []):
        lines.append(
            "| `{source_id}` | `{compatibility_surface}` | `{local_presence}` | {notes} |".format(
                source_id=row.get("source_id", ""),
                compatibility_surface=row.get("compatibility_surface", ""),
                local_presence=row.get("local_presence", ""),
                notes=", ".join(str(item) for item in row.get("notes", [])),
            )
        )
    _section(lines, "Owned Trusted", [row for row in skills if row.get("legitimacy_status") == "owned_trusted"])
    _section(lines, "Official Trusted", [row for row in skills if row.get("legitimacy_status") == "official_trusted"])
    _section(lines, "Needs Review", review_rows)
    _section(lines, "Blocked Hostile", [row for row in skills if row.get("legitimacy_status") == "blocked_hostile"])
    if review_rows:
        lines.extend(["", "## Review Notes", ""])
        for row in review_rows[:30]:
            reason = str(row.get("legitimacy_reason") or "No reason cached.")
            codes = ", ".join(f"`{code}`" for code in row.get("finding_codes", [])[:4]) or "_no finding codes_"
            lines.append(f"- `{row.get('name', '')}`: {reason} Findings: {codes}.")
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_inventory_snapshot()
    target = REPO_ROOT / "references" / "skill-vetting-report.md"
    target.write_text(render_report(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
