#!/usr/bin/env python3
"""Maintain a local skill trust ledger from observed outcomes."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

EVENT_WEIGHTS = {
    "success": 3,
    "warn": -4,
    "throttled": -7,
    "failure": -10,
    "disabled": -18,
    "quarantined": -20,
    "restored": 8,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record and report skill trust events")
    parser.add_argument(
        "--ledger",
        default="~/.codex/skills/.trust-ledger.local.json",
        help="Ledger JSON path",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Append a single trust event")
    record.add_argument("--skill", required=True, help="Skill name")
    record.add_argument(
        "--event",
        required=True,
        choices=tuple(sorted(EVENT_WEIGHTS.keys())),
        help="Event type",
    )
    record.add_argument("--source", default="manual", help="Event source")
    record.add_argument("--note", default="", help="Optional note")
    record.add_argument("--timestamp", default="", help="Optional timestamp (ISO8601)")
    record.add_argument("--json-out", default="", help="Optional JSON output path")
    record.add_argument("--format", choices=("table", "json"), default="table")

    ingest = subparsers.add_parser("ingest-arbiter", help="Ingest skill-arbiter JSON result")
    ingest.add_argument("--input", required=True, help="arbiter --json-out file path")
    ingest.add_argument("--source", default="skill-arbiter", help="Event source")
    ingest.add_argument("--json-out", default="", help="Optional JSON output path")
    ingest.add_argument("--format", choices=("table", "json"), default="table")

    report = subparsers.add_parser("report", help="Generate trust report")
    report.add_argument("--window-days", type=int, default=90, help="Lookback window")
    report.add_argument("--min-events", type=int, default=1, help="Minimum events per skill")
    report.add_argument("--json-out", default="", help="Optional JSON output path")
    report.add_argument("--format", choices=("table", "json"), default="table")

    return parser.parse_args()


def parse_timestamp(text: str) -> datetime:
    cleaned = str(text or "").strip()
    if not cleaned:
        return datetime.now(timezone.utc)

    candidate = cleaned.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {text!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "updated_at": now_iso(), "events": []}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ledger must be a JSON object")

    events = payload.get("events")
    if not isinstance(events, list):
        payload["events"] = []

    if "version" not in payload:
        payload["version"] = 1
    if "updated_at" not in payload:
        payload["updated_at"] = now_iso()

    return payload


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def append_event(ledger: dict[str, Any], *, skill: str, event: str, source: str, note: str, timestamp: str) -> dict[str, Any]:
    skill_name = str(skill).strip()
    if not skill_name:
        raise ValueError("skill is required")
    event_name = str(event).strip().lower()
    if event_name not in EVENT_WEIGHTS:
        raise ValueError(f"unsupported event: {event}")

    ts = parse_timestamp(timestamp)
    row = {
        "timestamp": ts.isoformat().replace("+00:00", "Z"),
        "skill": skill_name,
        "event": event_name,
        "weight": EVENT_WEIGHTS[event_name],
        "source": str(source).strip() or "unknown",
        "note": str(note or "").strip(),
    }

    events = ledger.setdefault("events", [])
    if not isinstance(events, list):
        raise ValueError("ledger events must be a list")
    events.append(row)
    ledger["updated_at"] = now_iso()
    return row


def ingest_arbiter(ledger: dict[str, Any], payload: dict[str, Any], source: str) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("arbiter JSON missing results[]")

    added: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill") or "").strip()
        action = str(item.get("action") or "").strip().lower()
        persistent = bool(item.get("persistent_nonzero"))
        max_rg = int(item.get("max_rg") or 0)

        if not skill:
            continue

        event = "success"
        note = f"action={action} max_rg={max_rg} persistent_nonzero={persistent}"

        if action in {"deleted", "blacklisted", "quarantined"}:
            event = "quarantined"
        elif action in {"kept", "promoted"} and not persistent and max_rg == 0:
            event = "success"
        elif action in {"kept", "promoted"} and persistent:
            event = "warn"
        elif action in {"kept", "promoted"} and max_rg > 0:
            event = "throttled"
        elif action in {"error", "failed"}:
            event = "failure"

        added.append(
            append_event(
                ledger,
                skill=skill,
                event=event,
                source=source,
                note=note,
                timestamp="",
            )
        )

    return added


def tier_for_score(score: int) -> str:
    if score >= 80:
        return "trusted"
    if score >= 60:
        return "observe"
    if score >= 40:
        return "restricted"
    return "blocked"


def build_report(ledger: dict[str, Any], window_days: int, min_events: int) -> dict[str, Any]:
    rows = ledger.get("events", [])
    if not isinstance(rows, list):
        rows = []

    anchor = datetime.now(timezone.utc)
    start = anchor - timedelta(days=max(int(window_days), 1) - 1)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill") or "").strip()
        if not skill:
            continue

        ts_raw = str(item.get("timestamp") or "").strip()
        try:
            ts = parse_timestamp(ts_raw)
        except ValueError:
            continue
        if ts < start:
            continue

        grouped.setdefault(skill, []).append(item)

    skills: list[dict[str, Any]] = []
    for skill, events in grouped.items():
        if len(events) < max(int(min_events), 1):
            continue

        score = 50
        counts: dict[str, int] = {}
        total_weight = 0
        for event in events:
            name = str(event.get("event") or "").strip().lower()
            weight = int(event.get("weight") or EVENT_WEIGHTS.get(name, 0))
            total_weight += weight
            score += weight
            counts[name] = counts.get(name, 0) + 1

        score = max(0, min(score, 100))
        tier = tier_for_score(score)

        skills.append(
            {
                "skill": skill,
                "score": score,
                "tier": tier,
                "events": len(events),
                "total_weight": total_weight,
                "counts": dict(sorted(counts.items())),
            }
        )

    skills.sort(key=lambda item: (item["score"], item["skill"]))

    recommendations: list[str] = []
    blocked = [item["skill"] for item in skills if item["tier"] == "blocked"]
    restricted = [item["skill"] for item in skills if item["tier"] == "restricted"]
    if blocked:
        recommendations.append("Keep blocked skills disabled until a clean validation cycle is recorded.")
    if restricted:
        recommendations.append("Require manual approval before invoking restricted skills.")
    if not recommendations:
        recommendations.append("Trust ledger is stable; continue periodic ingestion and review.")

    return {
        "generated_at": now_iso(),
        "window": {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": anchor.isoformat().replace("+00:00", "Z"),
            "days": max(int(window_days), 1),
        },
        "skills": skills,
        "recommendations": recommendations,
    }


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def render_record_table(payload: dict[str, Any]) -> str:
    row = payload["event"]
    return (
        f"recorded: skill={row['skill']} event={row['event']} weight={row['weight']} "
        f"source={row['source']} timestamp={row['timestamp']}"
    )


def render_ingest_table(payload: dict[str, Any]) -> str:
    lines = [f"ingested_events: {len(payload['events'])}"]
    for event in payload["events"]:
        lines.append(
            f"- skill={event['skill']} event={event['event']} weight={event['weight']} note={event['note']}"
        )
    return "\n".join(lines)


def render_report_table(payload: dict[str, Any]) -> str:
    lines = [
        "window: {start} -> {end} ({days}d)".format(**payload["window"]),
        "",
        "skill                              score  tier        events  counts",
        "---------------------------------  -----  ----------  ------  ------------------------------",
    ]
    for row in payload["skills"]:
        counts = ",".join(f"{key}:{value}" for key, value in row["counts"].items())
        lines.append(
            "{skill:<33}  {score:>5}  {tier:<10}  {events:>6}  {counts}".format(
                skill=row["skill"][:33],
                score=int(row["score"]),
                tier=row["tier"],
                events=int(row["events"]),
                counts=counts or "-",
            )
        )

    lines.append("")
    lines.append("recommendations:")
    for item in payload["recommendations"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    ledger_path = Path(args.ledger).expanduser().resolve()
    ledger = load_ledger(ledger_path)

    if args.command == "record":
        event = append_event(
            ledger,
            skill=args.skill,
            event=args.event,
            source=args.source,
            note=args.note,
            timestamp=args.timestamp,
        )
        save_ledger(ledger_path, ledger)
        payload = {"ledger": str(ledger_path), "event": event}
        write_json(args.json_out, payload)
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print(render_record_table(payload))
        return 0

    if args.command == "ingest-arbiter":
        arbiter_path = Path(args.input).expanduser().resolve()
        payload = json.loads(arbiter_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("arbiter JSON must be an object")
        events = ingest_arbiter(ledger, payload, args.source)
        save_ledger(ledger_path, ledger)
        out = {"ledger": str(ledger_path), "events": events, "source": str(arbiter_path)}
        write_json(args.json_out, out)
        if args.format == "json":
            print(json.dumps(out, indent=2, ensure_ascii=True))
        else:
            print(render_ingest_table(out))
        return 0

    if args.command == "report":
        out = build_report(ledger, args.window_days, args.min_events)
        out["ledger"] = str(ledger_path)
        write_json(args.json_out, out)
        if args.format == "json":
            print(json.dumps(out, indent=2, ensure_ascii=True))
        else:
            print(render_report_table(out))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
