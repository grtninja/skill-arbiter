from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from .contracts import CollaborationEvent, utc_now
from .paths import REPO_ROOT, collaboration_log_path
from .skill_game_runtime import record_payload as record_skill_game_payload
from .skill_game_runtime import recommended_targets as skill_game_recommended_targets

DEFAULT_TRUST_LEDGER = Path.home() / ".codex" / "skills" / ".trust-ledger.local.json"
VALID_OUTCOMES = {"success", "partial", "blocked", "failed"}
VALID_STABILITY = {"emerging", "repeatable", "stable"}
VALID_SKILL_ACTIONS = {"create", "upgrade", "consolidate"}
OUTCOME_TO_TRUST_EVENT = {
    "success": "success",
    "partial": "warn",
    "blocked": "throttled",
    "failed": "failure",
}


def _load_log() -> dict[str, Any]:
    path = collaboration_log_path()
    if not path.is_file():
        return {"version": 1, "updated_at": utc_now(), "events": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("collaboration log must be a JSON object")
    events = payload.get("events")
    if not isinstance(events, list):
        payload["events"] = []
    if "version" not in payload:
        payload["version"] = 1
    if "updated_at" not in payload:
        payload["updated_at"] = utc_now()
    return payload


def _save_log(payload: dict[str, Any]) -> None:
    path = collaboration_log_path()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _string_list(rows: object, *, field_name: str) -> list[str]:
    values: list[str] = []
    for row in rows or []:
        text = str(row or "").strip()
        if text:
            values.append(text)
    if not values and field_name in {"collaborators", "repo_scope"}:
        return values
    return list(dict.fromkeys(values))


def _normalize_skill_work(rows: object) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        action = str(row.get("action") or "").strip().lower()
        reason = str(row.get("reason") or "").strip()
        status = str(row.get("status") or "suggested").strip().lower()
        if not name or action not in VALID_SKILL_ACTIONS:
            continue
        items.append(
            {
                "name": name,
                "action": action,
                "reason": reason,
                "status": status or "suggested",
            }
        )
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["name"], item["action"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def read_collaboration_events(limit: int = 50) -> list[dict[str, Any]]:
    payload = _load_log()
    events = payload.get("events")
    if not isinstance(events, list):
        return []
    trimmed = [item for item in events if isinstance(item, dict)]
    return trimmed[-max(1, limit) :]


def _resolve_trust_ledger_script() -> Path | None:
    attempts = [
        REPO_ROOT / "skill-candidates" / "skill-trust-ledger" / "scripts" / "trust_ledger.py",
        Path.home() / ".codex" / "skills" / "skill-trust-ledger" / "scripts" / "trust_ledger.py",
    ]
    for attempt in attempts:
        if attempt.is_file():
            return attempt
    return None


def _record_trust_events(*, skills_used: list[str], outcome: str, note: str) -> dict[str, Any]:
    trust_event = OUTCOME_TO_TRUST_EVENT.get(outcome)
    script = _resolve_trust_ledger_script()
    if not skills_used or trust_event is None or script is None:
        return {
            "available": script is not None,
            "event": trust_event or "",
            "ledger": str(DEFAULT_TRUST_LEDGER),
            "records": [],
        }

    records: list[dict[str, Any]] = []
    for skill_name in skills_used:
        cmd = [
            sys.executable,
            str(script),
            "--ledger",
            str(DEFAULT_TRUST_LEDGER),
            "record",
            "--skill",
            skill_name,
            "--event",
            trust_event,
            "--source",
            "collaboration",
            "--note",
            note[:200],
            "--format",
            "json",
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            records.append(
                {
                    "skill": skill_name,
                    "status": "error",
                    "stderr": completed.stderr.strip(),
                }
            )
            continue
        try:
            payload = json.loads(completed.stdout.strip() or "{}")
        except json.JSONDecodeError:
            payload = {"raw_stdout": completed.stdout.strip()}
        records.append({"skill": skill_name, "status": "recorded", "payload": payload})
    return {
        "available": True,
        "event": trust_event,
        "ledger": str(DEFAULT_TRUST_LEDGER),
        "records": records,
    }


def _skill_work_recommendations(events: list[dict[str, Any]], inventory: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    inventory_rows = {
        str(row.get("name") or ""): row
        for row in inventory.get("skills", [])
        if isinstance(row, dict) and str(row.get("name") or "").strip()
    }
    scores: dict[tuple[str, str], dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        stability = str(event.get("stability") or "emerging").strip().lower()
        bonus = {"stable": 3, "repeatable": 2}.get(stability, 1)
        for item in event.get("proposed_skill_work", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            action = str(item.get("action") or "").strip().lower()
            if not name or action not in VALID_SKILL_ACTIONS:
                continue
            key = (name, action)
            row = scores.setdefault(
                key,
                {
                    "name": name,
                    "action": action,
                    "score": 0,
                    "reason": str(item.get("reason") or "").strip(),
                    "status": str(item.get("status") or "suggested").strip().lower() or "suggested",
                    "last_seen": str(event.get("created_at") or ""),
                },
            )
            row["score"] += bonus
            row["last_seen"] = str(event.get("created_at") or row["last_seen"])
            if not row["reason"]:
                row["reason"] = str(item.get("reason") or "").strip()
    ranked = sorted(scores.values(), key=lambda item: (-int(item["score"]), item["name"], item["action"]))
    results: list[dict[str, Any]] = []
    for item in ranked[: max(1, limit)]:
        inventory_row = inventory_rows.get(item["name"], {})
        results.append(
            {
                **item,
                "inventory_presence": str(inventory_row.get("local_presence") or "candidate_only"),
                "inventory_source_type": str(inventory_row.get("source_type") or "untracked"),
            }
        )
    return results


def status_payload(inventory: dict[str, Any], recent: int = 6) -> dict[str, Any]:
    events = read_collaboration_events(limit=200)
    recent_events = list(reversed(events[-max(1, recent) :]))
    stable_count = sum(1 for item in events if str(item.get("stability") or "") == "stable")
    return {
        "event_count": len(events),
        "stable_event_count": stable_count,
        "recent_events": recent_events,
        "recommended_skill_work": _skill_work_recommendations(events, inventory),
        "inventory_targets": skill_game_recommended_targets(inventory),
        "trust_ledger_available": _resolve_trust_ledger_script() is not None,
    }


def record_payload(
    *,
    inventory: dict[str, Any],
    host_id: str,
    task: str,
    outcome: str,
    collaborators: list[str] | None = None,
    repo_scope: list[str] | None = None,
    skills_used: list[str] | None = None,
    proposed_skill_work: list[dict[str, str]] | None = None,
    note: str = "",
    stability: str = "emerging",
    dry_run: bool = False,
) -> dict[str, Any]:
    task_name = str(task or "").strip()
    if not task_name:
        raise ValueError("task is required")
    normalized_outcome = str(outcome or "").strip().lower()
    if normalized_outcome not in VALID_OUTCOMES:
        raise ValueError(f"unsupported outcome: {outcome}")
    normalized_stability = str(stability or "emerging").strip().lower()
    if normalized_stability not in VALID_STABILITY:
        raise ValueError(f"unsupported stability: {stability}")

    event = CollaborationEvent(
        event_id=f"collab-{utc_now().replace(':', '').replace('-', '')}",
        task=task_name,
        outcome=normalized_outcome,
        host_id=host_id,
        collaborators=_string_list(collaborators or [], field_name="collaborators"),
        repo_scope=_string_list(repo_scope or [], field_name="repo_scope"),
        skills_used=_string_list(skills_used or [], field_name="skills_used"),
        proposed_skill_work=_normalize_skill_work(proposed_skill_work or []),
        note=str(note or "").strip(),
        stability=normalized_stability,
    )

    payload = _load_log()
    events = payload.setdefault("events", [])
    if not isinstance(events, list):
        raise ValueError("collaboration log events must be a list")
    if not dry_run:
        events.append(event.to_dict())
        payload["updated_at"] = utc_now()
        _save_log(payload)

    trust_payload = _record_trust_events(
        skills_used=event.skills_used,
        outcome=normalized_outcome,
        note=f"{task_name}: {event.note}".strip(": "),
    )
    skill_game = record_skill_game_payload(
        inventory=inventory,
        task=f"collaboration::{task_name}",
        required_skills=event.skills_used,
        used_skills=event.skills_used,
        arbiter_report="",
        audit_report="",
        enforcer_pass=True if event.skills_used else None,
        dry_run=dry_run,
    )
    status = status_payload(inventory)
    return {
        "event": event.to_dict(),
        "event_written": not dry_run,
        "trust_ledger": trust_payload,
        "skill_game": skill_game,
        **status,
    }
