#!/usr/bin/env python3
"""Analyze skill spend and emit budget actions (warn/throttle/disable)."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import statistics
from typing import Any

DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)

ACTION_ORDER = {"ok": 0, "warn": 1, "throttle": 2, "disable": 3}


@dataclass(frozen=True)
class UsageEvent:
    timestamp: datetime
    skill: str
    caller_skill: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    credits: float
    runtime_ms: float
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze skill usage costs and enforce budget actions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze invocation usage and produce policy actions")
    analyze.add_argument("--input", required=True, help="Usage CSV/JSON file path")
    analyze.add_argument("--window-days", type=int, default=30, help="Rolling analysis window in days")
    analyze.add_argument(
        "--credits-per-1k-tokens",
        type=float,
        default=0.0,
        help="Fallback credit rate when credits field is missing",
    )
    analyze.add_argument("--soft-daily-budget", type=float, default=0.0, help="Soft daily budget (warn/throttle)")
    analyze.add_argument("--hard-daily-budget", type=float, default=0.0, help="Hard daily budget (disable)")
    analyze.add_argument("--soft-window-budget", type=float, default=0.0, help="Soft rolling-window budget")
    analyze.add_argument("--hard-window-budget", type=float, default=0.0, help="Hard rolling-window budget")
    analyze.add_argument("--spike-multiplier", type=float, default=2.0, help="Daily spike threshold multiplier")
    analyze.add_argument("--loop-threshold", type=int, default=6, help="Consecutive caller->skill run threshold")
    analyze.add_argument("--chatter-threshold", type=int, default=20, help="Caller->skill pair frequency threshold")
    analyze.add_argument("--max-runtime-ms", type=float, default=45_000.0, help="P95 runtime guardrail")
    analyze.add_argument("--json-out", default="", help="Optional JSON report output path")
    analyze.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    decide = subparsers.add_parser("decide", help="Extract/override policy actions from an analysis JSON")
    decide.add_argument("--analysis-json", required=True, help="Analysis JSON path from analyze command")
    decide.add_argument(
        "--force-global-action",
        choices=("none", "warn", "throttle", "disable"),
        default="none",
        help="Optional global override escalation",
    )
    decide.add_argument("--json-out", default="", help="Optional JSON policy output path")
    decide.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    return parser.parse_args()


def parse_timestamp(raw: Any) -> datetime:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("missing timestamp")

    candidate = text.replace("Z", "+00:00")
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"unsupported timestamp format: {text!r}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_float(raw: Any, default: float = 0.0) -> float:
    text = str(raw or "").strip().lower().replace(",", "")
    text = text.replace("credits", "").strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def to_int(raw: Any, default: int = 0) -> int:
    value = to_float(raw, float(default))
    return int(value)


def _lowered(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).strip().lower(): value for key, value in row.items()}


def pick(row: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    lowered = _lowered(row)
    for key in keys:
        if key in lowered:
            return lowered[key]
    return default


def read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"input not found: {path}")

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("events"), list):
            return [item for item in payload["events"] if isinstance(item, dict)]
        raise ValueError("JSON input must be list[object] or {'events': [...]} ")

    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_events(path: Path, credits_per_1k_tokens: float) -> list[UsageEvent]:
    rows = read_rows(path)
    events: list[UsageEvent] = []
    for index, row in enumerate(rows, start=1):
        try:
            timestamp = parse_timestamp(
                pick(row, ("timestamp", "ts", "datetime", "time", "date", "day"))
            )
            skill = str(pick(row, ("skill", "skill_name", "callee_skill", "target_skill"), "")).strip()
            if not skill:
                raise ValueError("missing skill")

            caller_skill = str(
                pick(row, ("caller_skill", "source_skill", "parent_skill", "caller"), "")
            ).strip()

            prompt_tokens = to_int(pick(row, ("prompt_tokens", "input_tokens", "tokens_in"), 0), 0)
            completion_tokens = to_int(
                pick(row, ("completion_tokens", "output_tokens", "tokens_out"), 0),
                0,
            )
            total_tokens = to_int(pick(row, ("total_tokens", "tokens", "token_total"), 0), 0)
            if total_tokens <= 0:
                total_tokens = max(prompt_tokens + completion_tokens, 0)

            credits = to_float(pick(row, ("credits", "credit_cost", "credits_used", "cost"), ""), 0.0)
            if credits <= 0.0 and credits_per_1k_tokens > 0.0 and total_tokens > 0:
                credits = (total_tokens / 1000.0) * credits_per_1k_tokens

            runtime_ms = to_float(
                pick(row, ("runtime_ms", "duration_ms", "latency_ms", "runtime", "duration"), ""),
                0.0,
            )
            status = str(pick(row, ("status", "result", "outcome"), "unknown")).strip() or "unknown"
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"failed to parse row {index}: {exc}") from exc

        events.append(
            UsageEvent(
                timestamp=timestamp,
                skill=skill,
                caller_skill=caller_skill,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                credits=credits,
                runtime_ms=runtime_ms,
                status=status,
            )
        )

    events.sort(key=lambda item: item.timestamp)
    return events


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return float(statistics.quantiles(values, n=100, method="inclusive")[94])


def budget_pressure(current: float, soft: float, hard: float) -> str:
    if hard > 0 and current >= hard:
        return "disable"
    if soft > 0 and current >= soft:
        return "throttle"
    if soft > 0 and current >= (soft * 0.8):
        return "warn"
    return "ok"


def escalate(action: str, floor_action: str) -> str:
    if ACTION_ORDER[action] >= ACTION_ORDER[floor_action]:
        return action
    return floor_action


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    events = read_events(Path(args.input).expanduser().resolve(), args.credits_per_1k_tokens)
    if not events:
        raise ValueError("input contains no events")

    window_days = max(int(args.window_days), 1)
    anchor = max(event.timestamp for event in events)
    window_start = anchor - timedelta(days=window_days - 1)
    window_events = [event for event in events if event.timestamp >= window_start]

    if not window_events:
        raise ValueError("no events in requested window")

    skill_accum: dict[str, dict[str, Any]] = {}
    day_credits: dict[str, float] = {}
    pair_accum: dict[str, dict[str, Any]] = {}

    for event in window_events:
        skill = event.skill
        day_key = event.timestamp.date().isoformat()
        day_credits[day_key] = day_credits.get(day_key, 0.0) + event.credits

        if skill not in skill_accum:
            skill_accum[skill] = {
                "invocations": 0,
                "credits": 0.0,
                "tokens": 0,
                "runtimes": [],
                "day_credits": {},
                "status_counts": {},
            }
        row = skill_accum[skill]
        row["invocations"] += 1
        row["credits"] += event.credits
        row["tokens"] += event.total_tokens
        row["runtimes"].append(float(event.runtime_ms))
        row["day_credits"][day_key] = row["day_credits"].get(day_key, 0.0) + event.credits
        row["status_counts"][event.status] = row["status_counts"].get(event.status, 0) + 1

        if event.caller_skill:
            pair_key = f"{event.caller_skill}->{event.skill}"
            if pair_key not in pair_accum:
                pair_accum[pair_key] = {
                    "caller": event.caller_skill,
                    "skill": event.skill,
                    "invocations": 0,
                    "credits": 0.0,
                    "tokens": 0,
                    "runtimes": [],
                }
            pair = pair_accum[pair_key]
            pair["invocations"] += 1
            pair["credits"] += event.credits
            pair["tokens"] += event.total_tokens
            pair["runtimes"].append(float(event.runtime_ms))

    loop_events: list[dict[str, Any]] = []
    run_key = ""
    run_start = window_events[0].timestamp
    run_last = window_events[0].timestamp
    run_count = 0
    for event in window_events:
        key = f"{event.caller_skill}->{event.skill}" if event.caller_skill else ""
        same_stream = key and key == run_key and (event.timestamp - run_last).total_seconds() <= 600
        if same_stream:
            run_count += 1
            run_last = event.timestamp
            continue

        if run_key and run_count >= max(int(args.loop_threshold), 2):
            caller, skill = run_key.split("->", 1)
            loop_events.append(
                {
                    "pair": run_key,
                    "caller": caller,
                    "skill": skill,
                    "count": run_count,
                    "start": run_start.isoformat(),
                    "end": run_last.isoformat(),
                }
            )

        run_key = key
        run_start = event.timestamp
        run_last = event.timestamp
        run_count = 1 if key else 0

    if run_key and run_count >= max(int(args.loop_threshold), 2):
        caller, skill = run_key.split("->", 1)
        loop_events.append(
            {
                "pair": run_key,
                "caller": caller,
                "skill": skill,
                "count": run_count,
                "start": run_start.isoformat(),
                "end": run_last.isoformat(),
            }
        )

    chatter_pairs: list[dict[str, Any]] = []
    for key, item in pair_accum.items():
        invocations = int(item["invocations"])
        avg_runtime = sum(item["runtimes"]) / len(item["runtimes"]) if item["runtimes"] else 0.0
        avg_tokens = float(item["tokens"]) / invocations if invocations > 0 else 0.0
        if invocations >= max(int(args.chatter_threshold), 1) and avg_runtime <= 1_500.0 and avg_tokens <= 200.0:
            chatter_pairs.append(
                {
                    "pair": key,
                    "caller": item["caller"],
                    "skill": item["skill"],
                    "invocations": invocations,
                    "avg_runtime_ms": round(avg_runtime, 2),
                    "avg_tokens": round(avg_tokens, 2),
                }
            )

    total_credits = sum(float(item["credits"]) for item in skill_accum.values())
    total_tokens = sum(int(item["tokens"]) for item in skill_accum.values())
    total_invocations = sum(int(item["invocations"]) for item in skill_accum.values())

    avg_daily_credits = total_credits / window_days
    peak_day = ""
    peak_day_credits = 0.0
    if day_credits:
        peak_day, peak_day_credits = max(day_credits.items(), key=lambda item: item[1])

    global_daily_pressure = budget_pressure(avg_daily_credits, args.soft_daily_budget, args.hard_daily_budget)
    global_window_pressure = budget_pressure(total_credits, args.soft_window_budget, args.hard_window_budget)
    global_action = "ok"
    for candidate in (global_daily_pressure, global_window_pressure):
        if ACTION_ORDER[candidate] > ACTION_ORDER[global_action]:
            global_action = candidate

    loop_skill_set = {item["skill"] for item in loop_events}
    chatter_skill_set = {item["skill"] for item in chatter_pairs}

    skill_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []

    for skill, item in sorted(skill_accum.items(), key=lambda pair: pair[1]["credits"], reverse=True):
        invocations = int(item["invocations"])
        credits = float(item["credits"])
        tokens = int(item["tokens"])
        runtimes = [float(value) for value in item["runtimes"]]
        day_values = [float(value) for value in item["day_credits"].values()]

        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0.0
        p95_runtime = p95(runtimes)
        avg_daily_skill = sum(day_values) / max(len(day_values), 1)
        peak_daily_skill = max(day_values) if day_values else 0.0
        spike = bool(avg_daily_skill > 0 and peak_daily_skill >= (avg_daily_skill * max(args.spike_multiplier, 1.0)))

        share_percent = (credits / total_credits * 100.0) if total_credits > 0 else 0.0
        tokens_per_invocation = (tokens / invocations) if invocations > 0 else 0.0

        reason_codes: list[str] = []
        if spike:
            reason_codes.append("cost_spike")
        if skill in loop_skill_set:
            reason_codes.append("inefficient_loop")
        if skill in chatter_skill_set:
            reason_codes.append("agent_chatter")
        if p95_runtime >= float(args.max_runtime_ms):
            reason_codes.append("runtime_p95_high")
        if share_percent >= 25.0:
            reason_codes.append("high_spend_share")

        severity = 0
        if "inefficient_loop" in reason_codes:
            severity += 2
        if "agent_chatter" in reason_codes:
            severity += 2
        if "cost_spike" in reason_codes:
            severity += 1
        if "runtime_p95_high" in reason_codes:
            severity += 1
        if share_percent >= 40.0:
            severity += 2
        elif share_percent >= 25.0:
            severity += 1

        action = "ok"
        if severity >= 4:
            action = "disable"
        elif severity >= 2:
            action = "throttle"
        elif severity >= 1:
            action = "warn"

        if global_action == "warn":
            action = escalate(action, "warn")
        elif global_action == "throttle":
            action = escalate(action, "throttle")
        elif global_action == "disable":
            if share_percent >= 10.0:
                action = "disable"
            else:
                action = escalate(action, "throttle")

        skill_rows.append(
            {
                "skill": skill,
                "invocations": invocations,
                "credits": round(credits, 4),
                "credits_share_percent": round(share_percent, 2),
                "tokens": tokens,
                "tokens_per_invocation": round(tokens_per_invocation, 2),
                "avg_runtime_ms": round(avg_runtime, 2),
                "p95_runtime_ms": round(p95_runtime, 2),
                "avg_daily_credits": round(avg_daily_skill, 4),
                "peak_daily_credits": round(peak_daily_skill, 4),
                "status_counts": dict(sorted(item["status_counts"].items())),
                "reason_codes": sorted(set(reason_codes)),
                "proposed_action": action,
            }
        )
        policy_rows.append(
            {
                "skill": skill,
                "action": action,
                "reason_codes": sorted(set(reason_codes)),
            }
        )

    report = {
        "window": {
            "start": window_start.isoformat(),
            "end": anchor.isoformat(),
            "days": window_days,
            "events": len(window_events),
        },
        "totals": {
            "credits": round(total_credits, 4),
            "tokens": total_tokens,
            "invocations": total_invocations,
            "avg_daily_credits": round(avg_daily_credits, 4),
            "peak_day": peak_day,
            "peak_day_credits": round(float(peak_day_credits), 4),
        },
        "budgets": {
            "soft_daily_budget": round(float(args.soft_daily_budget), 4),
            "hard_daily_budget": round(float(args.hard_daily_budget), 4),
            "soft_window_budget": round(float(args.soft_window_budget), 4),
            "hard_window_budget": round(float(args.hard_window_budget), 4),
            "daily_pressure": global_daily_pressure,
            "window_pressure": global_window_pressure,
        },
        "skills": skill_rows,
        "chatter_pairs": sorted(chatter_pairs, key=lambda item: item["invocations"], reverse=True)[:30],
        "loop_events": sorted(loop_events, key=lambda item: item["count"], reverse=True)[:30],
        "policy": {
            "global_action": global_action,
            "actions": policy_rows,
            "soft_enforcement": [
                "warn => surface evidence and require explicit confirmation before heavy tasks",
                "throttle => cap expensive skill usage to focused scopes until next analysis",
                "disable => block execution except manual override after review",
            ],
        },
    }
    return report


def decide(args: argparse.Namespace) -> dict[str, Any]:
    analysis_path = Path(args.analysis_json).expanduser().resolve()
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("analysis JSON must be an object")

    policy = payload.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("analysis JSON missing policy object")

    actions = policy.get("actions")
    if not isinstance(actions, list):
        raise ValueError("analysis policy missing actions list")

    normalized: list[dict[str, Any]] = []
    for row in actions:
        if not isinstance(row, dict):
            continue
        skill = str(row.get("skill") or "").strip()
        action = str(row.get("action") or "ok").strip().lower()
        if not skill:
            continue
        if action not in ACTION_ORDER:
            action = "warn"
        normalized.append(
            {
                "skill": skill,
                "action": action,
                "reason_codes": [str(item) for item in row.get("reason_codes", []) if str(item).strip()],
            }
        )

    force_action = str(args.force_global_action).lower()
    if force_action not in {"none", "warn", "throttle", "disable"}:
        force_action = "none"

    if force_action != "none":
        for row in normalized:
            row["action"] = escalate(str(row["action"]), force_action)

    global_action = str(policy.get("global_action") or "ok").lower()
    if force_action != "none" and ACTION_ORDER[force_action] > ACTION_ORDER.get(global_action, 0):
        global_action = force_action

    summary = {
        "global_action": global_action,
        "actions": sorted(normalized, key=lambda item: (-ACTION_ORDER[item["action"]], item["skill"])),
        "enforced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_analysis": str(analysis_path),
    }
    return summary


def render_table_analysis(report: dict[str, Any]) -> str:
    lines = [
        "window: {start} -> {end} ({days}d, events={events})".format(**report["window"]),
        (
            "totals: credits={credits} tokens={tokens} invocations={invocations} "
            "avg_daily={avg_daily_credits} peak_day={peak_day}:{peak_day_credits}"
        ).format(**report["totals"]),
        (
            "budget pressure: daily={daily_pressure} window={window_pressure} "
            "global_action={global_action}"
        ).format(
            daily_pressure=report["budgets"]["daily_pressure"],
            window_pressure=report["budgets"]["window_pressure"],
            global_action=report["policy"]["global_action"],
        ),
        "",
        "skill                         action     credits     share%   invocations   p95_ms   reasons",
        "----------------------------  ---------  ----------  ------   -----------   -------  ------------------------------",
    ]
    for row in report["skills"]:
        reasons = ",".join(row["reason_codes"]) if row["reason_codes"] else "-"
        lines.append(
            "{skill:<28}  {action:<9}  {credits:>10.4f}  {share:>6.2f}   {inv:>11}   {p95:>7.1f}  {reasons}".format(
                skill=row["skill"][:28],
                action=row["proposed_action"],
                credits=float(row["credits"]),
                share=float(row["credits_share_percent"]),
                inv=int(row["invocations"]),
                p95=float(row["p95_runtime_ms"]),
                reasons=reasons,
            )
        )
    return "\n".join(lines)


def render_table_policy(policy: dict[str, Any]) -> str:
    lines = [
        f"global_action: {policy['global_action']}",
        "",
        "skill                         action     reasons",
        "----------------------------  ---------  ------------------------------",
    ]
    for row in policy["actions"]:
        reasons = ",".join(row["reason_codes"]) if row["reason_codes"] else "-"
        lines.append(
            "{skill:<28}  {action:<9}  {reasons}".format(
                skill=row["skill"][:28],
                action=row["action"],
                reasons=reasons,
            )
        )
    return "\n".join(lines)


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.command == "analyze":
        report = analyze(args)
        write_json(args.json_out, report)
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=True))
        else:
            print(render_table_analysis(report))
        return 0

    if args.command == "decide":
        policy = decide(args)
        write_json(args.json_out, policy)
        if args.format == "json":
            print(json.dumps(policy, indent=2, ensure_ascii=True))
        else:
            print(render_table_policy(policy))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
