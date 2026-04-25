from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .contracts import utc_now
from .paths import REPO_ROOT, collaboration_log_path, windows_no_window_subprocess_kwargs

DEFAULT_TRUST_LEDGER = Path.home() / ".codex" / "skills" / ".trust-ledger.local.json"
# Keep the public-readiness phrase "trust ledger" present in this runtime surface.
VALID_OUTCOMES = {"success", "partial", "blocked", "failed"}
VALID_STABILITY = {"emerging", "repeatable", "stable"}
VALID_SKILL_ACTIONS = {"create", "upgrade", "consolidate"}
OUTCOME_TO_TRUST_EVENT = {
    "success": "success",
    "partial": "warn",
    "blocked": "throttled",
    "failed": "failure",
}
COLLABORATION_CACHE_SECONDS = 2.5
MAX_COLLABORATORS_PER_RECORD = 10
MAX_REPO_SCOPE_PER_RECORD = 10
MAX_PROPOSED_WORK_PER_RECORD = 6
SUBAGENT_LOOP_WINDOW = 120
SUBAGENT_LOOP_DOMINANCE_LIMIT = 3
SUBAGENT_LOOP_SHARE_THRESHOLD = 0.70
KNOWN_RECURSIVE_SUBAGENTS = {"faraday", "lovelace", "fermat"}

_COLLAB_EVENTS_LOCK = threading.Lock()
_COLLAB_EVENTS_CACHE: dict[str, Any] = {"expires_at": 0.0, "events": None}
_COLLABORATION_IGNORE_ACTORS = {
    "",
    "local",
    "operator",
    "skill-arbiter",
    "skill_arbiter",
    "system",
    "skill-enforcer",
    "meshgpt-dcc",
    "meshgpt_admin",
    "meshgpt-admin",
}


def _to_event_list(payload: Any) -> list[dict[str, Any]]:
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        return []
    return [item for item in events if isinstance(item, dict)]


def _as_collaboration_name(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in _COLLABORATION_IGNORE_ACTORS:
        return ""
    return text


def _is_subagent_name(value: object) -> bool:
    name = _as_collaboration_name(value)
    return bool(name) and (name.startswith("subagent-") or name in KNOWN_RECURSIVE_SUBAGENTS)


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


def _bounded_string_list(rows: object, *, field_name: str, max_items: int) -> tuple[list[str], list[str]]:
    cap = max(1, int(max_items))
    if field_name == "collaborators":
        normalized = [_as_collaboration_name(row) for row in rows or []]
    else:
        normalized = [str(row or "").strip().lower() for row in rows or [] if str(row or "").strip()]
    values = list(dict.fromkeys([row for row in normalized if row]))
    clipped = len(values) - min(len(values), cap)
    if clipped <= 0:
        return values, []
    return values[:cap], [f"{field_name}_trimmed"]


def _bounded_skill_work(rows: object, *, max_items: int) -> tuple[list[dict[str, str]], list[str]]:
    cap = max(1, int(max_items))
    proposals = _normalize_skill_work(rows)
    clipped = len(proposals) - min(len(proposals), cap)
    if clipped <= 0:
        return proposals, []
    return proposals[:cap], ["proposed_skill_work_trimmed"]


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


def _load_events() -> list[dict[str, Any]]:
    return _to_event_list(_load_log())


def _save_log(payload: dict[str, Any]) -> None:
    with _COLLAB_EVENTS_LOCK:
        _COLLAB_EVENTS_CACHE["events"] = None
        _COLLAB_EVENTS_CACHE["expires_at"] = 0.0
    path = collaboration_log_path()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _cached_events() -> list[dict[str, Any]]:
    now = time.time()
    with _COLLAB_EVENTS_LOCK:
        events = _COLLAB_EVENTS_CACHE.get("events")
        if isinstance(events, list) and _COLLAB_EVENTS_CACHE.get("expires_at", 0.0) > now:
            return list(events)
        events = list(_load_events())
        _COLLAB_EVENTS_CACHE["events"] = events
        _COLLAB_EVENTS_CACHE["expires_at"] = now + COLLABORATION_CACHE_SECONDS
        return events


def read_collaboration_events(limit: int = 50) -> list[dict[str, Any]]:
    normalized_limit = max(1, int(limit) if isinstance(limit, int) else 1)
    return _cached_events()[-normalized_limit:]


def _collaboration_churn_metrics(events: list[dict[str, Any]], *, window_size: int = 120) -> dict[str, Any]:
    sample = events[-max(1, window_size) :]
    collaborator_counts = Counter()
    scope_counts = Counter()
    total = 0
    for row in sample:
        collaborators = row.get("collaborators")
        if isinstance(collaborators, list):
            normalized = [_as_collaboration_name(item) for item in collaborators]
            normalized = [item for item in normalized if item]
            if normalized:
                total += 1
                for item in set(normalized):
                    collaborator_counts[item] += 1
        scopes = row.get("repo_scope")
        if isinstance(scopes, list):
            scope_counts.update([str(item or "").strip().lower() for item in scopes if str(item or "").strip()])

    top_collaborators = [
        {"name": name, "event_count": int(count)}
        for name, count in collaborator_counts.most_common(4)
        if name
    ]
    dominant_count = top_collaborators[0]["event_count"] if top_collaborators else 0
    dominance_ratio = float(dominant_count) / total if total else 0.0
    possible_loop = dominant_count >= SUBAGENT_LOOP_DOMINANCE_LIMIT and dominance_ratio >= SUBAGENT_LOOP_SHARE_THRESHOLD
    stable_recent = total >= 6 and (sample[-1].get("stability") if sample else None) in {"stable", "repeatable", "emerging"}

    return {
        "window_events": int(total),
        "total_events_considered": int(len(sample)),
        "active_collaborator_count": int(len(collaborator_counts)),
        "active_collaborator_share": round(dominance_ratio, 3),
        "top_collaborators": top_collaborators,
        "dominant_collaborator": top_collaborators[0]["name"] if top_collaborators else "",
        "scope_diversity": int(len(scope_counts)),
        "possible_review_loop": bool(possible_loop),
        "stable_recent": bool(stable_recent),
        "assessment": "watch" if possible_loop else "ok" if total >= 2 else "idle",
    }


def _subagent_admission_assessment(events: list[dict[str, Any]]) -> dict[str, Any]:
    window = events[-min(len(events), SUBAGENT_LOOP_WINDOW) :]
    violations: list[dict[str, object]] = []
    active_subagents: list[dict[str, object]] = []
    subagent_counts: Counter[str] = Counter()
    task_repeats: Counter[tuple[str, tuple[str, ...]]] = Counter()

    for event in window:
        collaborators = [item for item in event.get("collaborators", []) if _as_collaboration_name(item)]
        repo_scope = [str(item or "").strip().lower() for item in event.get("repo_scope", []) if str(item or "").strip()]
        proposed_work = [item for item in event.get("proposed_skill_work", []) if isinstance(item, dict)]
        task = str(event.get("task") or "").strip().lower()

        if len(collaborators) > MAX_COLLABORATORS_PER_RECORD:
            violations.append({"type": "collaborator_burst", "count": len(collaborators), "limit": MAX_COLLABORATORS_PER_RECORD, "task": task})
        if len(repo_scope) > MAX_REPO_SCOPE_PER_RECORD:
            violations.append({"type": "repo_scope_burst", "count": len(repo_scope), "limit": MAX_REPO_SCOPE_PER_RECORD, "task": task})
        if len(proposed_work) > MAX_PROPOSED_WORK_PER_RECORD:
            violations.append({"type": "proposed_work_burst", "count": len(proposed_work), "limit": MAX_PROPOSED_WORK_PER_RECORD, "task": task})

        active_subagents_in_event = [item for item in collaborators if _is_subagent_name(item)]
        for name in active_subagents_in_event:
            subagent_counts[name] += 1
        if task:
            task_repeats[(task, tuple(active_subagents_in_event))] += 1

    for name, count in subagent_counts.most_common(6):
        active_subagents.append({"name": name, "event_count": int(count)})

    recommendations: list[str] = []
    if violations:
        recommendations.append("apply_bounded_workload_gate")
    for key, count in task_repeats.items():
        task_name, _ = key
        if count >= SUBAGENT_LOOP_DOMINANCE_LIMIT:
            recommendations.append(f"stagger_task_loop:{task_name}")
    if not violations and not task_repeats:
        recommendations.append("bounded_workload")

    return {
        "mode": "throttle" if violations else "bounded",
        "violation_count": len(violations),
        "violations": violations[:12],
        "recommendations": sorted(set(recommendations)),
        "active_subagents": active_subagents,
        "bounds": {
            "max_collaborators_per_event": MAX_COLLABORATORS_PER_RECORD,
            "max_repo_scope_per_event": MAX_REPO_SCOPE_PER_RECORD,
            "max_proposed_work_per_event": MAX_PROPOSED_WORK_PER_RECORD,
            "loop_window": SUBAGENT_LOOP_WINDOW,
        },
    }


def _candidate_intake_summary(inventory: dict[str, Any]) -> dict[str, Any]:
    rows = inventory.get("skills", [])
    if not isinstance(rows, list):
        return {
            "candidates": [],
            "total": 0,
            "counts": {"admitted": 0, "pending": 0, "rejected": 0},
        }
    recent_work = {str(item).strip().lower() for item in inventory.get("recent_work_skills", []) if str(item).strip()}
    candidates: list[dict[str, Any]] = []
    counts = {"admitted": 0, "pending": 0, "rejected": 0}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("source_type") or "") != "overlay_candidate":
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        notes = [str(item).strip().lower() for item in row.get("notes", []) if str(item).strip()]
        is_recent = "recent_work_relevant" in notes or (name.lower() in recent_work)
        if not is_recent:
            continue
        legitimacy = str(row.get("legitimacy_status") or "").strip().lower()
        recommended_action = str(row.get("recommended_action") or "").strip().lower()
        if legitimacy == "blocked_hostile":
            decision = "rejected"
        elif recommended_action in {"install_candidate", "keep"} and legitimacy != "blocked_hostile":
            decision = "admitted"
        else:
            decision = "pending"
        counts[decision] += 1
        candidates.append(
            {
                "name": name,
                "decision": decision,
                "origin": str(row.get("origin") or ""),
                "recommended_action": recommended_action,
                "legitimacy_status": legitimacy,
                "recent_work_relevant": is_recent,
            }
        )
    candidates.sort(key=lambda row: row["name"])
    return {
        "candidates": candidates,
        "total": len(candidates),
        "counts": counts,
    }


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
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            **windows_no_window_subprocess_kwargs(),
        )
        if completed.returncode != 0:
            records.append({"skill": skill_name, "status": "error", "stderr": completed.stderr.strip()})
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
