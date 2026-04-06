from __future__ import annotations

from . import collaboration_support as _support
from .contracts import CollaborationEvent, utc_now
from .quest_runtime import status_payload as quest_status_payload
from .skill_game_runtime import record_payload as record_skill_game_payload
from .skill_game_runtime import recommended_targets as skill_game_recommended_targets
from .stack_runtime import normalize_mx3_from_events, summarize_subagents_from_events

MAX_COLLABORATORS_PER_RECORD = _support.MAX_COLLABORATORS_PER_RECORD
MAX_PROPOSED_WORK_PER_RECORD = _support.MAX_PROPOSED_WORK_PER_RECORD
MAX_REPO_SCOPE_PER_RECORD = _support.MAX_REPO_SCOPE_PER_RECORD
VALID_OUTCOMES = _support.VALID_OUTCOMES
VALID_STABILITY = _support.VALID_STABILITY
_COLLAB_EVENTS_CACHE = _support._COLLAB_EVENTS_CACHE
_bounded_skill_work = _support._bounded_skill_work
_bounded_string_list = _support._bounded_string_list
_candidate_intake_summary = _support._candidate_intake_summary
_collaboration_churn_metrics = _support._collaboration_churn_metrics
_load_log = _support._load_log
_record_trust_events = _support._record_trust_events
_resolve_trust_ledger_script = _support._resolve_trust_ledger_script
_save_log = _support._save_log
_skill_work_recommendations = _support._skill_work_recommendations
_subagent_admission_assessment = _support._subagent_admission_assessment


def _run_support(func, *args, **kwargs):
    original_cache = _support._COLLAB_EVENTS_CACHE
    original_load_log = _support._load_log
    original_save_log = _support._save_log
    original_record_trust_events = _support._record_trust_events
    _support._COLLAB_EVENTS_CACHE = _COLLAB_EVENTS_CACHE
    _support._load_log = _load_log
    _support._save_log = _save_log
    _support._record_trust_events = _record_trust_events
    try:
        return func(*args, **kwargs)
    finally:
        _support._COLLAB_EVENTS_CACHE = original_cache
        _support._load_log = original_load_log
        _support._save_log = original_save_log
        _support._record_trust_events = original_record_trust_events


def read_collaboration_events(limit: int = 50):
    return _run_support(_support.read_collaboration_events, limit=limit)


def status_payload(inventory: dict[str, object], recent: int = 6) -> dict[str, object]:
    events = read_collaboration_events(limit=200)
    recent_events = list(reversed(events[-max(1, recent) :]))
    stable_count = sum(1 for item in events if str(item.get("stability") or "") == "stable")
    mx3_runtime = normalize_mx3_from_events(events)
    subagent_coordination = summarize_subagents_from_events(events, max_items=6)
    collaboration_churn = _collaboration_churn_metrics(events, window_size=120)
    subagent_admission = _subagent_admission_assessment(events)
    candidate_intake = _candidate_intake_summary(inventory)
    quests = quest_status_payload(inventory, recent=max(3, recent))
    return {
        "event_count": len(events),
        "stable_event_count": stable_count,
        "recent_events": recent_events,
        "recommended_skill_work": _skill_work_recommendations(events, inventory),
        "inventory_targets": skill_game_recommended_targets(inventory),
        "mx3_runtime": mx3_runtime,
        "subagent_coordination": subagent_coordination,
        "subagent_admission": subagent_admission,
        "trust_ledger_available": _resolve_trust_ledger_script() is not None,
        "churn": collaboration_churn,
        "candidate_intake": candidate_intake,
        "quest_summary": {
            "quest_count": int(quests.get("quest_count") or 0),
            "completed_count": int(quests.get("completed_count") or 0),
            "meta_harness_count": int(quests.get("meta_harness_count") or 0),
            "active_chains": quests.get("active_chains", []),
        },
    }


def record_payload(
    *,
    inventory: dict[str, object],
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
) -> dict[str, object]:
    task_name = str(task or "").strip()
    if not task_name:
        raise ValueError("task is required")
    normalized_outcome = str(outcome or "").strip().lower()
    if normalized_outcome not in VALID_OUTCOMES:
        raise ValueError(f"unsupported outcome: {outcome}")
    normalized_stability = str(stability or "emerging").strip().lower()
    if normalized_stability not in VALID_STABILITY:
        raise ValueError(f"unsupported stability: {stability}")

    collaborators_normalized, collaborators_trimmed = _bounded_string_list(
        collaborators or [],
        field_name="collaborators",
        max_items=MAX_COLLABORATORS_PER_RECORD,
    )
    repo_scope_normalized, repo_scope_trimmed = _bounded_string_list(
        repo_scope or [],
        field_name="repo_scope",
        max_items=MAX_REPO_SCOPE_PER_RECORD,
    )
    skills_used_normalized, skills_used_trimmed = _bounded_string_list(
        skills_used or [],
        field_name="skills_used",
        max_items=MAX_PROPOSED_WORK_PER_RECORD,
    )
    proposed_skill_work_normalized, proposed_skill_work_trimmed = _bounded_skill_work(
        proposed_skill_work or [],
        max_items=MAX_PROPOSED_WORK_PER_RECORD,
    )

    event = CollaborationEvent(
        event_id=f"collab-{utc_now().replace(':', '').replace('-', '')}",
        task=task_name,
        outcome=normalized_outcome,
        host_id=host_id,
        collaborators=collaborators_normalized,
        repo_scope=repo_scope_normalized,
        skills_used=skills_used_normalized,
        proposed_skill_work=proposed_skill_work_normalized,
        note=str(note or "").strip(),
        stability=normalized_stability,
    )
    event_metadata = sorted(set(collaborators_trimmed + repo_scope_trimmed + skills_used_trimmed + proposed_skill_work_trimmed))
    event_payload = event.to_dict()
    if event_metadata:
        event_payload["field_trims"] = event_metadata

    payload = _load_log()
    events = payload.setdefault("events", [])
    if not isinstance(events, list):
        raise ValueError("collaboration log events must be a list")
    if not dry_run:
        events.append(event_payload)
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
        "event": event_payload,
        "event_written": not dry_run,
        "subagent_admission": status.get("subagent_admission", {}),
        "trust_ledger": trust_payload,
        "skill_game": skill_game,
        **status,
    }
