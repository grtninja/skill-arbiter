#!/usr/bin/env python3
"""Checkpoint and resume deterministic workstream state."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

ALLOWED_STATUS = {"pending", "in_progress", "completed", "blocked"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Checkpoint and resume workstream state")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Initialize a new workstream state file")
    init_p.add_argument("--state-file", required=True)
    init_p.add_argument("--task", required=True)
    init_p.add_argument("--lane", action="append", default=[], help="Lane name (repeatable)")
    init_p.add_argument("--in-progress", default="", help="Optional lane to mark in_progress")
    init_p.add_argument("--json-out", default="")

    set_p = sub.add_parser("set", help="Update lane status/next-step and append evidence")
    set_p.add_argument("--state-file", required=True)
    set_p.add_argument(
        "--lane-status",
        action="append",
        default=[],
        help="Lane status assignment in form lane=status",
    )
    set_p.add_argument(
        "--lane-next",
        action="append",
        default=[],
        help="Lane next-step assignment in form lane=text",
    )
    set_p.add_argument("--artifact", action="append", default=[], help="Evidence artifact path")
    set_p.add_argument("--note", default="")
    set_p.add_argument("--json-out", default="")

    val_p = sub.add_parser("validate", help="Validate workstream invariants")
    val_p.add_argument("--state-file", required=True)
    val_p.add_argument("--json-out", default="")

    resume_p = sub.add_parser("resume", help="Compute deterministic next action")
    resume_p.add_argument("--state-file", required=True)
    resume_p.add_argument("--json-out", default="")

    return parser.parse_args()


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_assignment(raw: str, *, sep: str) -> tuple[str, str]:
    text = str(raw or "").strip()
    if sep not in text:
        raise ValueError(f"invalid assignment {raw!r}; expected lane{sep}value")
    left, right = text.split(sep, 1)
    lane = left.strip()
    value = right.strip()
    if not lane or not value:
        raise ValueError(f"invalid assignment {raw!r}; lane and value are required")
    return lane, value


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"state file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("state root must be an object")
    lanes = data.get("lanes")
    if not isinstance(lanes, list):
        raise ValueError("state lanes must be a list")
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now_iso()
    path.write_text(json.dumps(state, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def lane_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = state.get("lanes")
    if not isinstance(rows, list):
        raise ValueError("state lanes must be a list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        out[name] = row
    return out


def validate_state(state: dict[str, Any]) -> tuple[bool, list[str], dict[str, int]]:
    errors: list[str] = []
    rows = state.get("lanes")
    if not isinstance(rows, list):
        return False, ["state lanes must be a list"], {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}

    if not rows:
        errors.append("no lanes defined")

    seen_names: set[str] = set()
    in_progress_count = 0
    counts = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"lane row {index} is not an object")
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            errors.append(f"lane row {index} is missing a name")
            continue
        if name in seen_names:
            errors.append(f"duplicate lane name: {name}")
        else:
            seen_names.add(name)
        status = str(row.get("status") or "").strip()
        if status not in ALLOWED_STATUS:
            errors.append(f"invalid status for lane {name}: {status}")
            continue
        counts[status] += 1
        if status == "in_progress":
            in_progress_count += 1

    if in_progress_count > 1:
        errors.append("more than one lane is in_progress")

    return (not errors), errors, counts


def run_init(args: argparse.Namespace) -> dict[str, Any]:
    lanes_raw = [str(item).strip() for item in args.lane if str(item).strip()]
    if not lanes_raw:
        raise ValueError("--lane is required at least once")

    unique: list[str] = []
    seen: set[str] = set()
    for lane in lanes_raw:
        if lane in seen:
            continue
        seen.add(lane)
        unique.append(lane)

    in_progress_lane = str(args.in_progress or "").strip()
    if in_progress_lane and in_progress_lane not in seen:
        raise ValueError("--in-progress lane must be one of --lane values")

    now = now_iso()
    lanes: list[dict[str, Any]] = []
    for lane in unique:
        status = "in_progress" if lane == in_progress_lane else "pending"
        lanes.append(
            {
                "name": lane,
                "status": status,
                "next_step": "",
                "artifacts": [],
                "updated_at": now,
            }
        )

    state = {
        "task": str(args.task).strip(),
        "created_at": now,
        "updated_at": now,
        "lanes": lanes,
        "history": [
            {
                "timestamp": now,
                "event": "init",
                "note": "initialized workstream",
            }
        ],
    }
    save_state(Path(args.state_file).expanduser().resolve(), state)
    return state


def run_set(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.state_file).expanduser().resolve()
    state = load_state(path)
    lanes = lane_map(state)
    now = now_iso()
    touched_lanes: set[str] = set()

    def ensure_lane(name: str) -> dict[str, Any]:
        if name not in lanes:
            lanes[name] = {
                "name": name,
                "status": "pending",
                "next_step": "",
                "artifacts": [],
                "updated_at": now,
            }
            state.setdefault("lanes", []).append(lanes[name])
        return lanes[name]

    for token in args.lane_status:
        lane, status = parse_assignment(token, sep="=")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"invalid status: {status}")
        row = ensure_lane(lane)
        row["status"] = status
        row["updated_at"] = now
        touched_lanes.add(lane)

    for token in args.lane_next:
        lane, text = parse_assignment(token, sep="=")
        row = ensure_lane(lane)
        row["next_step"] = text
        row["updated_at"] = now
        touched_lanes.add(lane)

    artifacts = [str(item).strip() for item in args.artifact if str(item).strip()]
    if artifacts:
        # Attach evidence to touched lanes when specified, otherwise treat as a global checkpoint.
        target_lanes = sorted(touched_lanes) if touched_lanes else sorted(lanes.keys())
        for lane_name in target_lanes:
            lane = ensure_lane(lane_name)
            lane_artifacts = lane.setdefault("artifacts", [])
            if not isinstance(lane_artifacts, list):
                lane_artifacts = []
                lane["artifacts"] = lane_artifacts
            for item in artifacts:
                if item not in lane_artifacts:
                    lane_artifacts.append(item)

    history = state.setdefault("history", [])
    if not isinstance(history, list):
        history = []
        state["history"] = history
    history.append(
        {
            "timestamp": now,
            "event": "set",
            "note": str(args.note or "").strip(),
            "lane_status": args.lane_status,
            "lane_next": args.lane_next,
            "artifacts": artifacts,
        }
    )

    save_state(path, state)
    return state


def run_validate(args: argparse.Namespace) -> dict[str, Any]:
    state = load_state(Path(args.state_file).expanduser().resolve())
    ok, errors, counts = validate_state(state)
    return {
        "ok": ok,
        "errors": errors,
        "counts": counts,
    }


def run_resume(args: argparse.Namespace) -> dict[str, Any]:
    state = load_state(Path(args.state_file).expanduser().resolve())
    ok, errors, counts = validate_state(state)
    lanes = state.get("lanes")
    if not isinstance(lanes, list):
        lanes = []

    in_progress: dict[str, Any] | None = None
    first_pending: dict[str, Any] | None = None
    blocked = 0

    for row in lanes:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "").strip()
        if status == "in_progress" and in_progress is None:
            in_progress = row
        elif status == "pending" and first_pending is None:
            first_pending = row
        elif status == "blocked":
            blocked += 1

    action = "done"
    lane_name = ""
    next_step = ""

    if not ok:
        action = "invalid"
    elif in_progress is not None:
        action = "continue"
        lane_name = str(in_progress.get("name") or "")
        next_step = str(in_progress.get("next_step") or "")
    elif first_pending is not None:
        action = "start"
        lane_name = str(first_pending.get("name") or "")
        next_step = str(first_pending.get("next_step") or "")
    elif blocked > 0 and counts.get("completed", 0) < len(lanes):
        action = "blocked"

    return {
        "ok": ok,
        "errors": errors,
        "counts": counts,
        "action": action,
        "lane": lane_name,
        "next_step": next_step,
        "task": str(state.get("task") or ""),
    }


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            payload = run_init(args)
            result = {"ok": True, "command": "init", "task": payload.get("task", "")}
            write_json(args.json_out, payload)
            print("workstream_resume: initialized")
            print(f"task={payload.get('task','')}")
            return 0
        if args.command == "set":
            payload = run_set(args)
            result = {"ok": True, "command": "set", "task": payload.get("task", "")}
            write_json(args.json_out, payload)
            print("workstream_resume: updated")
            print(f"task={payload.get('task','')}")
            return 0
        if args.command == "validate":
            result = run_validate(args)
            write_json(args.json_out, result)
            print("workstream_resume: " + ("valid" if result["ok"] else "invalid"))
            if not result["ok"]:
                for item in result["errors"]:
                    print(f"error:{item}")
                return 1
            return 0
        if args.command == "resume":
            result = run_resume(args)
            write_json(args.json_out, result)
            print("workstream_resume: " + result["action"])
            print(f"task={result['task']}")
            if result["lane"]:
                print(f"lane={result['lane']}")
            if result["next_step"]:
                print(f"next_step={result['next_step']}")
            if not result["ok"]:
                for item in result["errors"]:
                    print(f"error:{item}")
                return 1
            if result["action"] in {"blocked", "invalid"}:
                return 1
            return 0
        raise ValueError(f"unknown command: {args.command}")
    except ValueError as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
