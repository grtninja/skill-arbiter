#!/usr/bin/env python3
"""Score skill workflow compliance and persist an XP ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_LEDGER = Path.home() / ".codex" / "skills" / ".skill-game-ledger.json"
DEFAULT_REQUIRED_SKILLS = [
    "skill-hub",
    "skill-common-sense-engineering",
    "usage-watcher",
    "skill-cost-credit-governor",
    "skill-cold-start-warm-path-optimizer",
    "skill-installer-plus",
    "skill-auditor",
    "skill-enforcer",
    "skill-arbiter-lockdown-admission",
]


@dataclass
class Breakdown:
    """One scoring component."""

    category: str
    points: int
    detail: str


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Track skill workflow XP and levels")
    parser.add_argument("--task", default="unspecified", help="Task label for the score event")
    parser.add_argument(
        "--ledger",
        default=str(DEFAULT_LEDGER),
        help="Ledger JSON path (default: ~/.codex/skills/.skill-game-ledger.json)",
    )
    parser.add_argument(
        "--required-skill",
        action="append",
        default=[],
        help="Required workflow skill (repeatable; default chain used when omitted)",
    )
    parser.add_argument(
        "--used-skill",
        action="append",
        default=[],
        help="Skill used for this task (repeatable)",
    )
    parser.add_argument("--arbiter-report", default="", help="Path to skill-arbiter JSON report")
    parser.add_argument("--audit-report", default="", help="Path to skill-auditor JSON report")
    parser.add_argument(
        "--enforcer-pass",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Set true/false when skill-enforcer policy check was run",
    )
    parser.add_argument("--show", action="store_true", help="Show current ledger status without recording")
    parser.add_argument("--recent", type=int, default=5, help="Number of recent events to display with --show")
    parser.add_argument("--dry-run", action="store_true", help="Compute score without writing ledger")
    parser.add_argument("--bonus-points", type=int, default=0, help="Optional bounded bonus XP, for example from quest completion")
    parser.add_argument("--bonus-label", default="", help="Label for optional bonus XP")
    parser.add_argument("--context-json", default="", help="Optional JSON object to attach as event context")
    return parser.parse_args()


def unique_ordered(values: list[str]) -> list[str]:
    """Return deduped values preserving order."""

    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        item = raw.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def level_and_progress(total_xp: int) -> tuple[int, int, int]:
    """Return level, XP into current level, and XP needed for next level."""

    level = 1
    needed = 250
    remaining = max(total_xp, 0)
    while remaining >= needed:
        remaining -= needed
        level += 1
        needed += 100
    return level, remaining, needed


def load_json(path: Path) -> dict[str, object]:
    """Load a JSON object from path."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"failed to read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"json root must be object: {path}")
    return payload


def load_ledger(path: Path) -> dict[str, object]:
    """Load or initialize ledger."""

    if not path.is_file():
        return {
            "version": 1,
            "total_xp": 0,
            "level": 1,
            "streak": 0,
            "best_streak": 0,
            "events": [],
        }
    payload = load_json(path)
    events = payload.get("events")
    if not isinstance(events, list):
        payload["events"] = []
    for key, default in (
        ("version", 1),
        ("total_xp", 0),
        ("level", 1),
        ("streak", 0),
        ("best_streak", 0),
    ):
        if not isinstance(payload.get(key), int):
            payload[key] = default
    return payload


def score_required(required: list[str], used: list[str]) -> tuple[int, list[str], Breakdown]:
    """Score required skill compliance."""

    if not used:
        return (
            0,
            required,
            Breakdown(
                category="workflow",
                points=0,
                detail="no --used-skill entries provided; workflow compliance not scored",
            ),
        )

    used_set = set(used)
    hits = [name for name in required if name in used_set]
    missing = [name for name in required if name not in used_set]
    points = (len(hits) * 100) - (len(missing) * 140)
    detail = f"hits={len(hits)} missing={len(missing)}"
    return points, missing, Breakdown(category="workflow", points=points, detail=detail)


def score_arbiter(path_text: str) -> tuple[int, bool, Breakdown]:
    """Score arbiter evidence."""

    if not path_text:
        return 0, False, Breakdown(category="arbiter", points=0, detail="no arbiter report provided")

    path = Path(path_text).expanduser()
    payload = load_json(path)
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError(f"arbiter report missing results list: {path}")
    if not results:
        return -40, False, Breakdown(category="arbiter", points=-40, detail="empty results list")

    points = 0
    pass_count = 0
    fail_count = 0
    for item in results:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip()
        max_rg = item.get("max_rg")
        persistent = item.get("persistent_nonzero")
        if action == "kept" and persistent is False and isinstance(max_rg, int) and max_rg <= 3:
            pass_count += 1
            if max_rg == 0:
                points += 60
            elif max_rg <= 1:
                points += 45
            else:
                points += 30
        else:
            fail_count += 1
            points -= 80

    all_pass = fail_count == 0 and pass_count > 0
    if all_pass:
        points += 40
    detail = f"pass={pass_count} fail={fail_count}"
    return points, all_pass, Breakdown(category="arbiter", points=points, detail=detail)


def score_auditor(path_text: str) -> tuple[int, bool, Breakdown]:
    """Score auditor evidence."""

    if not path_text:
        return 0, False, Breakdown(category="auditor", points=0, detail="no auditor report provided")

    path = Path(path_text).expanduser()
    payload = load_json(path)
    high_count = payload.get("high_count")
    medium_count = payload.get("medium_count")
    low_count = payload.get("low_count")
    if not isinstance(high_count, int) or not isinstance(medium_count, int) or not isinstance(low_count, int):
        raise ValueError(f"auditor report missing status counts: {path}")

    points = 0
    if high_count == 0:
        points += 60
    else:
        points -= high_count * 120
    if medium_count == 0:
        points += 20
    else:
        points -= medium_count * 40
    if low_count == 0:
        points += 10
    detail = f"high={high_count} medium={medium_count} low={low_count}"
    all_pass = high_count == 0
    return points, all_pass, Breakdown(category="auditor", points=points, detail=detail)


def score_enforcer(flag: bool | None) -> tuple[int, bool, Breakdown]:
    """Score skill-enforcer lane."""

    if flag is None:
        return 0, False, Breakdown(category="enforcer", points=0, detail="no enforcer result provided")
    if flag:
        return 50, True, Breakdown(category="enforcer", points=50, detail="policy lane passed")
    return -120, False, Breakdown(category="enforcer", points=-120, detail="policy lane failed")


def print_status(ledger: dict[str, object], recent: int) -> None:
    """Print current ledger state."""

    total_xp = int(ledger.get("total_xp", 0))
    level, progress_xp, next_needed = level_and_progress(total_xp)
    streak = int(ledger.get("streak", 0))
    best_streak = int(ledger.get("best_streak", 0))
    print(f"total_xp={total_xp}")
    print(f"level={level}")
    print(f"level_progress={progress_xp}/{next_needed}")
    print(f"streak={streak}")
    print(f"best_streak={best_streak}")
    events = ledger.get("events")
    if not isinstance(events, list) or recent <= 0:
        return
    print("recent_events:")
    for item in events[-recent:]:
        if not isinstance(item, dict):
            continue
        task = item.get("task", "unknown")
        delta = item.get("xp_delta", 0)
        stamp = item.get("timestamp", "")
        clear_run = bool(item.get("clear_run", False))
        print(f"- {stamp} task={task} xp_delta={delta} clear_run={str(clear_run).lower()}")


def compute_score_event(
    *,
    task: str,
    ledger: dict[str, object],
    required_skills: list[str] | None = None,
    used_skills: list[str] | None = None,
    arbiter_report: str = "",
    audit_report: str = "",
    enforcer_pass: bool | None = None,
    bonus_points: int = 0,
    bonus_label: str = "",
    context: dict[str, object] | None = None,
) -> dict[str, object]:
    """Compute one score event without writing the ledger."""

    required = unique_ordered(required_skills or []) or DEFAULT_REQUIRED_SKILLS
    used = unique_ordered(used_skills or [])
    breakdown: list[Breakdown] = []

    workflow_points, missing_required, workflow_breakdown = score_required(required, used)
    breakdown.append(workflow_breakdown)

    arbiter_points, arbiter_ok, arbiter_breakdown = score_arbiter(arbiter_report)
    auditor_points, auditor_ok, auditor_breakdown = score_auditor(audit_report)
    breakdown.append(arbiter_breakdown)
    breakdown.append(auditor_breakdown)

    enforcer_points, _enforcer_ok, enforcer_breakdown = score_enforcer(enforcer_pass)
    breakdown.append(enforcer_breakdown)

    clear_workflow = bool(used) and not missing_required
    clear_run = clear_workflow and arbiter_ok and auditor_ok and (enforcer_pass is not False)

    bonus = 0
    if clear_run:
        current_streak = int(ledger.get("streak", 0)) + 1
        bonus = 150 + min(current_streak, 5) * 25
        breakdown.append(Breakdown(category="combo", points=bonus, detail=f"full-chain streak={current_streak}"))
        streak = current_streak
    else:
        streak = 0

    extra_bonus = max(-250, min(250, int(bonus_points or 0)))
    if extra_bonus:
        label = str(bonus_label or "manual_bonus").strip() or "manual_bonus"
        breakdown.append(Breakdown(category="bonus", points=extra_bonus, detail=label))

    xp_delta = workflow_points + arbiter_points + auditor_points + enforcer_points + bonus + extra_bonus
    xp_delta = max(-1000, min(1000, xp_delta))
    total_xp = max(0, int(ledger.get("total_xp", 0)) + xp_delta)
    level, progress_xp, next_needed = level_and_progress(total_xp)
    best_streak = max(int(ledger.get("best_streak", 0)), streak)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "task": task,
        "required_skills": required,
        "used_skills": used,
        "missing_required_skills": missing_required,
        "clear_run": clear_run,
        "xp_delta": xp_delta,
        "total_xp": total_xp,
        "level": level,
        "streak": streak,
        "breakdown": [asdict(item) for item in breakdown],
        "arbiter_report": arbiter_report,
        "audit_report": audit_report,
        "enforcer_pass": enforcer_pass,
        "context": context or {},
    }
    return {
        "event": event,
        "required": required,
        "used": used,
        "missing_required": missing_required,
        "clear_run": clear_run,
        "xp_delta": xp_delta,
        "total_xp": total_xp,
        "level": level,
        "level_progress": progress_xp,
        "level_next_needed": next_needed,
        "streak": streak,
        "best_streak": best_streak,
        "breakdown": [asdict(item) for item in breakdown],
    }


def record_score_event(
    *,
    ledger_path: Path,
    task: str,
    required_skills: list[str] | None = None,
    used_skills: list[str] | None = None,
    arbiter_report: str = "",
    audit_report: str = "",
    enforcer_pass: bool | None = None,
    dry_run: bool = False,
    bonus_points: int = 0,
    bonus_label: str = "",
    context: dict[str, object] | None = None,
) -> dict[str, object]:
    """Compute and optionally persist one score event."""

    ledger = load_ledger(ledger_path)
    payload = compute_score_event(
        task=task,
        ledger=ledger,
        required_skills=required_skills,
        used_skills=used_skills,
        arbiter_report=arbiter_report,
        audit_report=audit_report,
        enforcer_pass=enforcer_pass,
        bonus_points=bonus_points,
        bonus_label=bonus_label,
        context=context,
    )
    if not dry_run:
        events = ledger.get("events")
        if not isinstance(events, list):
            events = []
        events.append(payload["event"])
        if len(events) > 200:
            events = events[-200:]
        ledger["events"] = events
        ledger["total_xp"] = payload["total_xp"]
        ledger["level"] = payload["level"]
        ledger["streak"] = payload["streak"]
        ledger["best_streak"] = payload["best_streak"]
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=True), encoding="utf-8")
    payload["ledger_path"] = str(ledger_path)
    payload["ledger_written"] = not dry_run
    return payload


def ledger_status(ledger_path: Path, recent: int = 5) -> dict[str, object]:
    """Return current ledger status without recording a new event."""

    ledger = load_ledger(ledger_path)
    total_xp = int(ledger.get("total_xp", 0))
    level, progress_xp, next_needed = level_and_progress(total_xp)
    events = ledger.get("events")
    recent_events = events[-max(0, recent):] if isinstance(events, list) else []
    return {
        "ledger_path": str(ledger_path),
        "total_xp": total_xp,
        "level": level,
        "level_progress": progress_xp,
        "level_next_needed": next_needed,
        "streak": int(ledger.get("streak", 0)),
        "best_streak": int(ledger.get("best_streak", 0)),
        "recent_events": recent_events,
        "event_count": len(events) if isinstance(events, list) else 0,
    }


def main() -> int:
    """CLI entrypoint."""

    args = parse_args()
    ledger_path = Path(args.ledger).expanduser()

    try:
        ledger = load_ledger(ledger_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.show:
        print_status(ledger, args.recent)
        return 0

    context_payload: dict[str, object] | None = None
    if args.context_json:
        try:
            loaded_context = json.loads(args.context_json)
        except json.JSONDecodeError as exc:
            print(f"error: invalid --context-json: {exc}", file=sys.stderr)
            return 2
        if not isinstance(loaded_context, dict):
            print("error: --context-json must decode to an object", file=sys.stderr)
            return 2
        context_payload = loaded_context

    try:
        payload = record_score_event(
            ledger_path=ledger_path,
            task=args.task,
            required_skills=args.required_skill,
            used_skills=args.used_skill,
            arbiter_report=args.arbiter_report,
            audit_report=args.audit_report,
            enforcer_pass=args.enforcer_pass,
            dry_run=args.dry_run,
            bonus_points=args.bonus_points,
            bonus_label=args.bonus_label,
            context=context_payload,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"task={args.task}")
    print(f"xp_delta={payload['xp_delta']}")
    print(f"total_xp={payload['total_xp']}")
    print(f"level={payload['level']}")
    print(f"level_progress={payload['level_progress']}/{payload['level_next_needed']}")
    print(f"streak={payload['streak']}")
    print(f"best_streak={payload['best_streak']}")
    print(f"clear_run={str(payload['clear_run']).lower()}")
    missing_required = payload["missing_required"]
    print(f"missing_required={','.join(missing_required) if missing_required else 'none'}")
    for item in payload["breakdown"]:
        print(f"score[{item['category']}]={item['points']} ({item['detail']})")
    if args.dry_run:
        print("ledger_write=skipped (--dry-run)")
    else:
        print(f"ledger_write={ledger_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
