#!/usr/bin/env python3
"""Usage watcher: analyze credit usage and generate spend guardrails."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%b %d, %Y",
    "%B %d, %Y",
)


@dataclass(frozen=True)
class UsageEvent:
    day: date
    service: str
    credits_used: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze usage and build credit control guardrails")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze usage history from CSV/JSON")
    analyze.add_argument("--input", required=True, help="Path to usage CSV or JSON")
    analyze.add_argument("--window-days", type=int, default=30, help="Rolling analysis window in days")
    analyze.add_argument("--daily-budget", type=float, default=0.0, help="Optional daily credits budget")
    analyze.add_argument("--weekly-budget", type=float, default=0.0, help="Optional weekly credits budget")
    analyze.add_argument("--credits-remaining", type=float, default=-1.0, help="Optional remaining credits balance")
    analyze.add_argument(
        "--five-hour-limit-remaining",
        type=float,
        default=-1.0,
        help="Optional 5-hour limit remaining percent (0-100)",
    )
    analyze.add_argument(
        "--weekly-limit-remaining",
        type=float,
        default=-1.0,
        help="Optional weekly limit remaining percent (0-100)",
    )
    analyze.add_argument("--json-out", default="", help="Optional report JSON output path")
    analyze.add_argument("--format", choices=("table", "json"), default="table", help="Output format")

    plan = subparsers.add_parser("plan", help="Generate budget mode caps")
    plan.add_argument("--monthly-budget", type=float, required=True, help="Monthly credits budget")
    plan.add_argument("--reserve-percent", type=float, default=20.0, help="Reserve percentage to protect")
    plan.add_argument("--work-days-per-week", type=float, default=5.0, help="Expected active work days/week")
    plan.add_argument("--sessions-per-day", type=float, default=3.0, help="Expected coding sessions/day")
    plan.add_argument(
        "--burst-multiplier",
        type=float,
        default=1.5,
        help="Allowable temporary burst multiplier above per-session cap",
    )
    plan.add_argument("--json-out", default="", help="Optional report JSON output path")
    plan.add_argument("--format", choices=("table", "json"), default="table", help="Output format")

    return parser.parse_args()


def parse_day(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("empty date value")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise ValueError(f"unsupported date format: {value!r}") from exc


def parse_credits(value: Any) -> float:
    text = str(value).strip().lower()
    text = text.replace("credits", "")
    text = text.replace(",", "")
    text = text.strip()
    if not text:
        raise ValueError("empty credits value")
    return float(text)


def normalize_service(value: Any) -> str:
    text = str(value).strip()
    return text if text else "unknown"


def read_events(path: Path) -> list[UsageEvent]:
    if not path.is_file():
        raise FileNotFoundError(f"input not found: {path}")

    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows: list[dict[str, Any]]
        if isinstance(payload, list):
            rows = [item for item in payload if isinstance(item, dict)]
        elif isinstance(payload, dict) and isinstance(payload.get("events"), list):
            rows = [item for item in payload["events"] if isinstance(item, dict)]
        else:
            raise ValueError("json input must be list[object] or {\"events\": [...]} ")
        return parse_rows(rows)

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(item) for item in reader]
    return parse_rows(rows)


def pick_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        if key in lowered:
            return lowered[key]
    raise KeyError(f"missing keys: {keys}")


def parse_rows(rows: list[dict[str, Any]]) -> list[UsageEvent]:
    events: list[UsageEvent] = []
    for index, row in enumerate(rows, start=1):
        try:
            day_value = pick_value(row, ("date", "day", "timestamp"))
            service_value = pick_value(row, ("service", "source", "product"))
            credits_value = pick_value(row, ("credits used", "credits_used", "credits", "usage", "amount"))
            event = UsageEvent(
                day=parse_day(str(day_value)),
                service=normalize_service(service_value),
                credits_used=parse_credits(credits_value),
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"failed to parse row {index}: {exc}") from exc
        events.append(event)

    events.sort(key=lambda item: (item.day, item.service))
    return events


def budget_status(current: float, budget: float) -> dict[str, Any]:
    if budget <= 0:
        return {"status": "unset", "ratio": None, "budget": 0.0, "current": current}

    ratio = current / budget if budget > 0 else 0.0
    if ratio > 1.0:
        status = "red"
    elif ratio > 0.8:
        status = "yellow"
    else:
        status = "green"
    return {
        "status": status,
        "ratio": round(ratio, 4),
        "budget": round(budget, 4),
        "current": round(current, 4),
    }


def remaining_status(percent: float) -> dict[str, Any]:
    if percent < 0:
        return {"status": "unset", "percent": None}
    if percent <= 10:
        status = "red"
    elif percent <= 25:
        status = "yellow"
    else:
        status = "green"
    return {"status": status, "percent": round(percent, 2)}


def analyze_usage(args: argparse.Namespace) -> dict[str, Any]:
    events = read_events(Path(args.input).expanduser().resolve())
    if not events:
        raise ValueError("input contains no usage rows")

    window_days = max(args.window_days, 1)
    anchor_day = max(event.day for event in events)
    window_start = anchor_day - timedelta(days=window_days - 1)
    window_events = [event for event in events if event.day >= window_start]

    daily_totals: dict[str, float] = {}
    service_totals: dict[str, float] = {}
    for event in window_events:
        key = event.day.isoformat()
        daily_totals[key] = daily_totals.get(key, 0.0) + event.credits_used
        service_totals[event.service] = service_totals.get(event.service, 0.0) + event.credits_used

    total_credits = sum(daily_totals.values())
    avg_daily_window = total_credits / window_days
    weekly_run_rate = avg_daily_window * 7.0
    projected_30d = avg_daily_window * 30.0

    peak_day = ""
    peak_credits = 0.0
    if daily_totals:
        peak_day, peak_credits = max(daily_totals.items(), key=lambda item: item[1])

    credits_runway_days = None
    if args.credits_remaining >= 0 and avg_daily_window > 0:
        credits_runway_days = args.credits_remaining / avg_daily_window

    daily_budget = budget_status(avg_daily_window, max(args.daily_budget, 0.0))
    weekly_budget = budget_status(weekly_run_rate, max(args.weekly_budget, 0.0))
    five_hour_remaining = remaining_status(args.five_hour_limit_remaining)
    weekly_remaining = remaining_status(args.weekly_limit_remaining)

    recommendations: list[str] = []
    if weekly_budget["status"] == "red" or weekly_remaining["status"] == "red":
        recommendations.append(
            "Enable Lean Mode immediately: narrow task scope, avoid broad refactors, and run one verification pass per change set."
        )
    if daily_budget["status"] in {"yellow", "red"}:
        recommendations.append(
            "Shift exploration to deterministic scripts and cached artifacts before sending additional model-heavy prompts."
        )
    if five_hour_remaining["status"] in {"yellow", "red"}:
        recommendations.append(
            "Split work into asynchronous chunks and queue only high-priority tasks until the 5-hour bucket recovers."
        )
    if not recommendations:
        recommendations.append("Usage is within guardrails. Keep standard mode and reassess at least once per day.")

    recommendations.append(
        "Prefer targeted file lookups and bounded index/query workflows over repeated full-repo scans."
    )

    service_rows = []
    for service in sorted(service_totals.keys()):
        credits = service_totals[service]
        share = (credits / total_credits * 100.0) if total_credits > 0 else 0.0
        service_rows.append(
            {
                "service": service,
                "credits": round(credits, 4),
                "share_percent": round(share, 2),
            }
        )

    day_rows = [
        {"date": key, "credits": round(value, 4)}
        for key, value in sorted(daily_totals.items(), key=lambda item: item[0])
    ]

    return {
        "window": {
            "start": window_start.isoformat(),
            "end": anchor_day.isoformat(),
            "days": window_days,
            "rows": len(window_events),
        },
        "summary": {
            "total_credits": round(total_credits, 4),
            "avg_daily_credits": round(avg_daily_window, 4),
            "weekly_run_rate": round(weekly_run_rate, 4),
            "projected_30d": round(projected_30d, 4),
            "peak_day": peak_day,
            "peak_day_credits": round(peak_credits, 4),
            "credits_remaining": round(args.credits_remaining, 4) if args.credits_remaining >= 0 else None,
            "credits_runway_days": round(credits_runway_days, 2) if credits_runway_days is not None else None,
        },
        "status": {
            "daily_budget": daily_budget,
            "weekly_budget": weekly_budget,
            "five_hour_limit_remaining": five_hour_remaining,
            "weekly_limit_remaining": weekly_remaining,
        },
        "services": service_rows,
        "daily": day_rows,
        "recommendations": recommendations,
    }


def build_budget_plan(args: argparse.Namespace) -> dict[str, Any]:
    if args.monthly_budget <= 0:
        raise ValueError("--monthly-budget must be > 0")
    if args.reserve_percent < 0 or args.reserve_percent >= 100:
        raise ValueError("--reserve-percent must be between 0 and <100")
    if args.work_days_per_week <= 0:
        raise ValueError("--work-days-per-week must be > 0")
    if args.sessions_per_day <= 0:
        raise ValueError("--sessions-per-day must be > 0")
    if args.burst_multiplier < 1.0:
        raise ValueError("--burst-multiplier must be >= 1.0")

    reserve = args.monthly_budget * (args.reserve_percent / 100.0)
    usable = args.monthly_budget - reserve
    work_days_month = args.work_days_per_week * 4.33
    calendar_daily = usable / 30.0
    workday_daily = usable / work_days_month
    per_session = workday_daily / args.sessions_per_day
    surge_session = per_session * args.burst_multiplier

    recommendations = [
        "Set hard stop at or below surge session cap for non-critical work.",
        "Use economy mode by default for discovery and planning; escalate only for final implementation blocks.",
        "Recompute the plan weekly using fresh usage history to avoid end-of-cycle overruns.",
    ]
    if args.reserve_percent < 15:
        recommendations.append("Increase reserve to at least 15% to absorb unexpected spikes.")

    modes = [
        {
            "mode": "economy",
            "session_cap": round(per_session * 0.6, 4),
            "intent": "triage, planning, and narrow edits",
        },
        {
            "mode": "standard",
            "session_cap": round(per_session, 4),
            "intent": "normal feature and fix workflows",
        },
        {
            "mode": "surge",
            "session_cap": round(surge_session, 4),
            "intent": "high-priority deadlines only",
        },
    ]

    return {
        "inputs": {
            "monthly_budget": round(args.monthly_budget, 4),
            "reserve_percent": round(args.reserve_percent, 2),
            "work_days_per_week": round(args.work_days_per_week, 2),
            "sessions_per_day": round(args.sessions_per_day, 2),
            "burst_multiplier": round(args.burst_multiplier, 2),
        },
        "caps": {
            "reserved_credits": round(reserve, 4),
            "usable_credits": round(usable, 4),
            "calendar_daily_cap": round(calendar_daily, 4),
            "workday_daily_cap": round(workday_daily, 4),
            "session_cap": round(per_session, 4),
            "surge_session_cap": round(surge_session, 4),
        },
        "modes": modes,
        "recommendations": recommendations,
    }


def print_kv_table(rows: list[tuple[str, str]]) -> None:
    key_width = max(len(key) for key, _ in rows)
    for key, value in rows:
        print(f"{key.ljust(key_width)} : {value}")


def render_analyze_table(report: dict[str, Any]) -> None:
    summary = report["summary"]
    status = report["status"]
    window = report["window"]

    print("Summary")
    print_kv_table(
        [
            ("window", f"{window['start']} -> {window['end']} ({window['days']} days)"),
            ("rows", str(window["rows"])),
            ("total_credits", str(summary["total_credits"])),
            ("avg_daily_credits", str(summary["avg_daily_credits"])),
            ("weekly_run_rate", str(summary["weekly_run_rate"])),
            ("projected_30d", str(summary["projected_30d"])),
            ("peak_day", f"{summary['peak_day']} ({summary['peak_day_credits']})"),
            (
                "credits_runway_days",
                "n/a" if summary["credits_runway_days"] is None else str(summary["credits_runway_days"]),
            ),
        ]
    )

    print("\nStatus")
    print_kv_table(
        [
            (
                "daily_budget",
                f"{status['daily_budget']['status']} (current={status['daily_budget']['current']}, budget={status['daily_budget']['budget']})",
            ),
            (
                "weekly_budget",
                f"{status['weekly_budget']['status']} (current={status['weekly_budget']['current']}, budget={status['weekly_budget']['budget']})",
            ),
            (
                "five_hour_remaining",
                f"{status['five_hour_limit_remaining']['status']} ({status['five_hour_limit_remaining']['percent']})",
            ),
            (
                "weekly_remaining",
                f"{status['weekly_limit_remaining']['status']} ({status['weekly_limit_remaining']['percent']})",
            ),
        ]
    )

    print("\nService Breakdown")
    if not report["services"]:
        print("(none)")
    else:
        for row in report["services"]:
            print(f"- {row['service']}: {row['credits']} credits ({row['share_percent']}%)")

    print("\nRecommendations")
    for item in report["recommendations"]:
        print(f"- {item}")


def render_plan_table(report: dict[str, Any]) -> None:
    inputs = report["inputs"]
    caps = report["caps"]

    print("Plan Inputs")
    print_kv_table([(key, str(value)) for key, value in inputs.items()])

    print("\nBudget Caps")
    print_kv_table([(key, str(value)) for key, value in caps.items()])

    print("\nMode Caps")
    for mode in report["modes"]:
        print(f"- {mode['mode']}: {mode['session_cap']} ({mode['intent']})")

    print("\nRecommendations")
    for item in report["recommendations"]:
        print(f"- {item}")


def maybe_write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        if args.command == "analyze":
            report = analyze_usage(args)
            maybe_write_json(args.json_out, report)
            if args.format == "json":
                print(json.dumps(report, indent=2, ensure_ascii=True))
            else:
                render_analyze_table(report)
            return 0

        if args.command == "plan":
            report = build_budget_plan(args)
            maybe_write_json(args.json_out, report)
            if args.format == "json":
                print(json.dumps(report, indent=2, ensure_ascii=True))
            else:
                render_plan_table(report)
            return 0

        print(f"error: unsupported command {args.command}")
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
