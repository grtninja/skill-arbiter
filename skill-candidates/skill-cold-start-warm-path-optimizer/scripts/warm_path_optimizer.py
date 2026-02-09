#!/usr/bin/env python3
"""Measure cold-start penalties and generate warm-path plans."""

from __future__ import annotations

import argparse
import csv
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze cold vs warm skill performance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Compute cold/warm metrics from execution logs")
    analyze.add_argument("--input", required=True, help="Execution log CSV/JSON path")
    analyze.add_argument("--window-days", type=int, default=30, help="Rolling window size")
    analyze.add_argument("--cold-penalty-min-ms", type=float, default=800.0, help="Minimum cold penalty for prewarm")
    analyze.add_argument("--min-invocations", type=int, default=3, help="Minimum invocations to consider prewarm")
    analyze.add_argument(
        "--rare-skill-max-invocations",
        type=int,
        default=2,
        help="Skills at or below this count are considered rare",
    )
    analyze.add_argument(
        "--never-auto-penalty-ms",
        type=float,
        default=3_000.0,
        help="Cold penalty threshold to recommend never-auto-invoke",
    )
    analyze.add_argument("--json-out", default="", help="Optional JSON output path")
    analyze.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    plan = subparsers.add_parser("plan", help="Build a prewarm plan from an analysis report")
    plan.add_argument("--analysis-json", required=True, help="Analyze JSON output path")
    plan.add_argument("--max-prewarm", type=int, default=10, help="Maximum prewarm skills")
    plan.add_argument("--json-out", default="", help="Optional JSON output path")
    plan.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    return parser.parse_args()


def parse_timestamp(raw: Any) -> datetime:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("missing timestamp")
    text = text.replace("Z", "+00:00")

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"unsupported timestamp format: {text!r}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_bool(raw: Any) -> bool | None:
    text = str(raw or "").strip().lower()
    if not text:
        return None
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def to_float(raw: Any, default: float = 0.0) -> float:
    text = str(raw or "").strip().lower().replace(",", "")
    text = text.replace("ms", "").strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def lowered(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).strip().lower(): value for key, value in row.items()}


def pick(row: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    data = lowered(row)
    for key in keys:
        if key in data:
            return data[key]
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


def quantile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    index = max(min(pct, 100), 1) - 1
    return float(statistics.quantiles(values, n=100, method="inclusive")[index])


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    rows = read_rows(Path(args.input).expanduser().resolve())
    if not rows:
        raise ValueError("input contains no rows")

    parsed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        try:
            timestamp = parse_timestamp(pick(row, ("timestamp", "ts", "datetime", "time", "date", "day")))
            skill = str(pick(row, ("skill", "skill_name", "target_skill", "callee_skill"), "")).strip()
            if not skill:
                raise ValueError("missing skill")
            duration_ms = to_float(
                pick(row, ("duration_ms", "runtime_ms", "latency_ms", "duration", "runtime"), ""),
                0.0,
            )
            if duration_ms < 0:
                duration_ms = 0.0

            cold_flag = parse_bool(pick(row, ("cold_start", "cold", "is_cold_start"), ""))
            cache_hit = parse_bool(pick(row, ("cache_hit", "warm_hit", "hit"), ""))
            status = str(pick(row, ("status", "result", "outcome"), "unknown")).strip() or "unknown"
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"failed to parse row {index}: {exc}") from exc

        parsed_rows.append(
            {
                "timestamp": timestamp,
                "skill": skill,
                "duration_ms": duration_ms,
                "cold_flag": cold_flag,
                "cache_hit": cache_hit,
                "status": status,
            }
        )

    parsed_rows.sort(key=lambda item: item["timestamp"])

    window_days = max(int(args.window_days), 1)
    anchor = max(item["timestamp"] for item in parsed_rows)
    window_start = anchor - timedelta(days=window_days - 1)
    items = [item for item in parsed_rows if item["timestamp"] >= window_start]
    if not items:
        raise ValueError("no rows in requested window")

    seen_skill: set[str] = set()
    accum: dict[str, dict[str, Any]] = {}

    for item in items:
        skill = str(item["skill"])
        if skill not in accum:
            accum[skill] = {
                "cold_durations": [],
                "warm_durations": [],
                "invocations": 0,
                "status_counts": {},
            }

        cold_flag = item["cold_flag"]
        if cold_flag is None:
            cache_hit = item["cache_hit"]
            if cache_hit is not None:
                cold_flag = not cache_hit
            else:
                cold_flag = skill not in seen_skill
        seen_skill.add(skill)

        bucket = accum[skill]
        bucket["invocations"] += 1
        bucket["status_counts"][item["status"]] = bucket["status_counts"].get(item["status"], 0) + 1

        if cold_flag:
            bucket["cold_durations"].append(float(item["duration_ms"]))
        else:
            bucket["warm_durations"].append(float(item["duration_ms"]))

    skill_rows: list[dict[str, Any]] = []
    prewarm_candidates: list[dict[str, Any]] = []
    never_auto: list[dict[str, Any]] = []

    for skill, bucket in sorted(accum.items(), key=lambda pair: pair[0]):
        cold = [float(x) for x in bucket["cold_durations"]]
        warm = [float(x) for x in bucket["warm_durations"]]

        cold_p50 = quantile(cold, 50)
        cold_p95 = quantile(cold, 95)
        warm_p50 = quantile(warm, 50)
        warm_p95 = quantile(warm, 95)

        cold_penalty = max(cold_p50 - warm_p50, 0.0)
        ratio = (cold_p50 / warm_p50) if warm_p50 > 0 else None
        invocations = int(bucket["invocations"])

        if invocations >= max(int(args.min_invocations), 1) and cold_penalty >= float(args.cold_penalty_min_ms):
            prewarm_candidates.append(
                {
                    "skill": skill,
                    "cold_penalty_ms": round(cold_penalty, 2),
                    "invocations": invocations,
                    "priority_score": round(cold_penalty * invocations, 2),
                }
            )

        if invocations <= max(int(args.rare_skill_max_invocations), 1) and cold_penalty >= float(args.never_auto_penalty_ms):
            never_auto.append(
                {
                    "skill": skill,
                    "invocations": invocations,
                    "cold_penalty_ms": round(cold_penalty, 2),
                }
            )

        skill_rows.append(
            {
                "skill": skill,
                "invocations": invocations,
                "cold_count": len(cold),
                "warm_count": len(warm),
                "cold_p50_ms": round(cold_p50, 2),
                "cold_p95_ms": round(cold_p95, 2),
                "warm_p50_ms": round(warm_p50, 2),
                "warm_p95_ms": round(warm_p95, 2),
                "cold_penalty_ms": round(cold_penalty, 2),
                "cold_to_warm_ratio": round(ratio, 3) if ratio is not None else None,
                "status_counts": dict(sorted(bucket["status_counts"].items())),
            }
        )

    prewarm_candidates.sort(key=lambda item: (-item["priority_score"], item["skill"]))
    never_auto.sort(key=lambda item: (-item["cold_penalty_ms"], item["skill"]))

    recommendations: list[str] = []
    if prewarm_candidates:
        recommendations.append("Prewarm top penalty skills before high-volume sessions.")
    if never_auto:
        recommendations.append("Disable auto-invoke for rare high-penalty skills.")
    if not recommendations:
        recommendations.append("Cold/warm profile is stable under configured thresholds.")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "window": {
            "start": window_start.isoformat(),
            "end": anchor.isoformat(),
            "days": window_days,
            "rows": len(items),
        },
        "thresholds": {
            "cold_penalty_min_ms": float(args.cold_penalty_min_ms),
            "min_invocations": max(int(args.min_invocations), 1),
            "rare_skill_max_invocations": max(int(args.rare_skill_max_invocations), 1),
            "never_auto_penalty_ms": float(args.never_auto_penalty_ms),
        },
        "skills": sorted(skill_rows, key=lambda item: (-item["cold_penalty_ms"], -item["invocations"], item["skill"])),
        "prewarm_candidates": prewarm_candidates,
        "never_auto_invoke": never_auto,
        "recommendations": recommendations,
    }
    return report


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    analysis_path = Path(args.analysis_json).expanduser().resolve()
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("analysis JSON must be an object")

    candidates = payload.get("prewarm_candidates")
    never_auto = payload.get("never_auto_invoke")
    if not isinstance(candidates, list) or not isinstance(never_auto, list):
        raise ValueError("analysis JSON missing prewarm_candidates/never_auto_invoke")

    max_prewarm = max(int(args.max_prewarm), 1)
    selected = [item for item in candidates if isinstance(item, dict)][:max_prewarm]

    steps: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        skill = str(row.get("skill") or "").strip()
        if not skill:
            continue
        steps.append(
            {
                "step": index,
                "skill": skill,
                "action": "prewarm",
                "note": "Invoke once with bounded prompt before normal workload.",
                "priority_score": row.get("priority_score"),
            }
        )

    for row in never_auto:
        if not isinstance(row, dict):
            continue
        skill = str(row.get("skill") or "").strip()
        if not skill:
            continue
        steps.append(
            {
                "step": len(steps) + 1,
                "skill": skill,
                "action": "disable_auto_invoke",
                "note": "Require manual trigger for rare high cold-penalty skill.",
                "cold_penalty_ms": row.get("cold_penalty_ms"),
            }
        )

    plan = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_analysis": str(analysis_path),
        "max_prewarm": max_prewarm,
        "steps": steps,
    }
    return plan


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def render_analysis_table(report: dict[str, Any]) -> str:
    lines = [
        "window: {start} -> {end} ({days}d, rows={rows})".format(**report["window"]),
        "",
        "skill                         invocations  cold_p50  warm_p50  penalty_ms  ratio",
        "----------------------------  -----------  --------  --------  ----------  ------",
    ]

    for row in report["skills"]:
        ratio = "-" if row["cold_to_warm_ratio"] is None else f"{row['cold_to_warm_ratio']:.3f}"
        lines.append(
            "{skill:<28}  {inv:>11}  {cold:>8.2f}  {warm:>8.2f}  {penalty:>10.2f}  {ratio:>6}".format(
                skill=row["skill"][:28],
                inv=int(row["invocations"]),
                cold=float(row["cold_p50_ms"]),
                warm=float(row["warm_p50_ms"]),
                penalty=float(row["cold_penalty_ms"]),
                ratio=ratio,
            )
        )

    lines.append("")
    prewarm_names = ", ".join(item["skill"] for item in report["prewarm_candidates"]) or "none"
    never_auto_names = ", ".join(item["skill"] for item in report["never_auto_invoke"]) or "none"
    lines.append(f"prewarm_candidates: {prewarm_names}")
    lines.append(f"never_auto_invoke: {never_auto_names}")
    return "\n".join(lines)


def render_plan_table(plan: dict[str, Any]) -> str:
    lines = [
        f"source_analysis: {plan['source_analysis']}",
        "",
        "step  action               skill                         note",
        "----  -------------------  ----------------------------  -----------------------------------------------",
    ]
    for row in plan["steps"]:
        lines.append(
            "{step:>4}  {action:<19}  {skill:<28}  {note}".format(
                step=int(row["step"]),
                action=str(row["action"]),
                skill=str(row["skill"])[:28],
                note=str(row["note"]),
            )
        )
    if not plan["steps"]:
        lines.append("(no plan steps generated)")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    if args.command == "analyze":
        report = analyze(args)
        write_json(args.json_out, report)
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=True))
        else:
            print(render_analysis_table(report))
        return 0

    if args.command == "plan":
        plan = build_plan(args)
        write_json(args.json_out, plan)
        if args.format == "json":
            print(json.dumps(plan, indent=2, ensure_ascii=True))
        else:
            print(render_plan_table(plan))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
