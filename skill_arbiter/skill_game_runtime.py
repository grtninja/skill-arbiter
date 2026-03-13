from __future__ import annotations

from pathlib import Path

from scripts.skill_game import DEFAULT_LEDGER, ledger_status, record_score_event
from .paths import REPO_ROOT


LEGACY_LEVELS_PATH = REPO_ROOT / "references" / "skill-progression.md"


def original_skill_levels(path: Path | None = None) -> list[dict[str, object]]:
    target = path or LEGACY_LEVELS_PATH
    if not target.is_file():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    in_table = False
    rows: list[dict[str, object]] = []
    for line in lines:
        if line.strip() == "## Current core levels":
            in_table = True
            continue
        if not in_table:
            continue
        if not line.strip():
            if rows:
                break
            continue
        if line.startswith("| ---"):
            continue
        if not line.startswith("|"):
            if rows:
                break
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 3 or parts[0] == "Skill":
            continue
        name = parts[0].strip("` ")
        try:
            level = int(parts[1])
        except ValueError:
            continue
        rows.append(
            {
                "name": name,
                "level": level,
                "notes": parts[2],
            }
        )
    rows.sort(key=lambda row: (-int(row["level"]), str(row["name"])))
    return rows


def _priority_for_skill(row: dict[str, object]) -> tuple[int, str]:
    source_type = str(row.get("source_type") or "")
    drift_state = str(row.get("drift_state") or "")
    notes = {str(item) for item in (row.get("notes") or [])}
    name = str(row.get("name") or "")
    ownership = str(row.get("ownership") or "")
    if source_type == "overlay_candidate" and "recent_work_relevant" in notes:
        return 100, f"{name}: recent-work skill candidate waiting for admit or upgrade."
    if source_type == "overlay_candidate":
        return 80, f"{name}: repo-tracked skill candidate can be promoted into the live stack."
    if drift_state == "missing_local_builtin":
        return 65, f"{name}: official baseline skill is missing locally and can be reconciled."
    if ownership == "official_builtin" and source_type == "installed_skill":
        return 50, f"{name}: official built-in can be upgraded with a trusted local overlay or add-on."
    if str(row.get("ownership") or "") == "repo_owned" and source_type == "installed_skill":
        return 40, f"{name}: owned installed skill is a good upgrade/refactor candidate."
    return 0, ""


def recommended_targets(inventory: dict[str, object], limit: int = 6) -> list[dict[str, object]]:
    rows: list[tuple[int, dict[str, object]]] = []
    for row in inventory.get("skills", []):
        if not isinstance(row, dict):
            continue
        priority, reason = _priority_for_skill(row)
        if priority <= 0:
            continue
        rows.append(
            (
                priority,
                {
                    "name": str(row.get("name") or ""),
                    "priority": priority,
                    "source_type": str(row.get("source_type") or ""),
                    "ownership": str(row.get("ownership") or ""),
                    "reason": reason,
                },
            )
        )
    rows.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [row for _, row in rows[: max(1, limit)]]


def status_payload(inventory: dict[str, object], ledger_path: Path | None = None, recent: int = 5) -> dict[str, object]:
    path = ledger_path or DEFAULT_LEDGER
    payload = ledger_status(path, recent=recent)
    levels = original_skill_levels()
    payload["recommended_targets"] = recommended_targets(inventory)
    payload["original_skill_levels"] = levels
    payload["original_skill_count"] = len(levels)
    payload["inventory_skill_count"] = int(inventory.get("skill_count") or 0)
    payload["incident_count"] = int(inventory.get("incident_count") or 0)
    return payload


def record_payload(
    *,
    inventory: dict[str, object],
    ledger_path: Path | None = None,
    task: str,
    required_skills: list[str] | None = None,
    used_skills: list[str] | None = None,
    arbiter_report: str = "",
    audit_report: str = "",
    enforcer_pass: bool | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    path = ledger_path or DEFAULT_LEDGER
    payload = record_score_event(
        ledger_path=path,
        task=task,
        required_skills=required_skills,
        used_skills=used_skills,
        arbiter_report=arbiter_report,
        audit_report=audit_report,
        enforcer_pass=enforcer_pass,
        dry_run=dry_run,
    )
    levels = original_skill_levels()
    payload["recommended_targets"] = recommended_targets(inventory)
    payload["original_skill_levels"] = levels
    payload["original_skill_count"] = len(levels)
    return payload
