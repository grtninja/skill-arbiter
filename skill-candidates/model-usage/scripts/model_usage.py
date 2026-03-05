#!/usr/bin/env python3
"""Summarize local CodexBar usage cost by model."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def run_codexbar_cost(provider: str) -> list[dict[str, Any]]:
    cmd = ["codexbar", "cost", "--format", "json", "--provider", provider]
    try:
        output = subprocess.check_output(cmd, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("codexbar not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"codexbar cost failed (exit {exc.returncode})") from exc
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid codexbar JSON output: {exc}") from exc
    if not isinstance(payload, list):
        raise RuntimeError("expected codexbar payload as JSON array")
    return payload


def load_payload(input_path: str, provider: str) -> dict[str, Any]:
    if input_path:
        raw = sys.stdin.read() if input_path == "-" else Path(input_path).read_text(encoding="utf-8")
        data = json.loads(raw)
    else:
        data = run_codexbar_cost(provider)

    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get("provider") == provider:
                return entry
        raise RuntimeError(f"provider not found in payload: {provider}")
    raise RuntimeError("unsupported payload type")


@dataclass
class ModelCost:
    model: str
    cost: float


def parse_daily_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("daily")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def filter_by_days(entries: list[dict[str, Any]], days: int | None) -> list[dict[str, Any]]:
    if not days:
        return entries
    cutoff = date.today() - timedelta(days=days - 1)
    out: list[dict[str, Any]] = []
    for entry in entries:
        day = entry.get("date")
        if not isinstance(day, str):
            continue
        parsed = parse_date(day)
        if parsed and parsed >= cutoff:
            out.append(entry)
    return out


def aggregate_costs(entries: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for entry in entries:
        breakdowns = entry.get("modelBreakdowns")
        if not isinstance(breakdowns, list):
            continue
        for item in breakdowns:
            if not isinstance(item, dict):
                continue
            model = item.get("modelName")
            cost = item.get("cost")
            if isinstance(model, str) and isinstance(cost, (int, float)):
                totals[model] = totals.get(model, 0.0) + float(cost)
    return totals


def pick_current_model(entries: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if not entries:
        return None, None
    sorted_entries = sorted(entries, key=lambda row: str(row.get("date") or ""))
    for entry in reversed(sorted_entries):
        breakdowns = entry.get("modelBreakdowns")
        if isinstance(breakdowns, list) and breakdowns:
            scored: list[ModelCost] = []
            for item in breakdowns:
                if not isinstance(item, dict):
                    continue
                model = item.get("modelName")
                cost = item.get("cost")
                if isinstance(model, str) and isinstance(cost, (int, float)):
                    scored.append(ModelCost(model=model, cost=float(cost)))
            if scored:
                scored.sort(key=lambda row: row.cost, reverse=True)
                day = entry.get("date")
                return scored[0].model, day if isinstance(day, str) else None
        models_used = entry.get("modelsUsed")
        if isinstance(models_used, list) and models_used:
            last = models_used[-1]
            if isinstance(last, str):
                day = entry.get("date")
                return last, day if isinstance(day, str) else None
    return None, None


def latest_day_cost(entries: list[dict[str, Any]], model: str) -> tuple[str | None, float | None]:
    if not entries:
        return None, None
    sorted_entries = sorted(entries, key=lambda row: str(row.get("date") or ""))
    for entry in reversed(sorted_entries):
        breakdowns = entry.get("modelBreakdowns")
        if not isinstance(breakdowns, list):
            continue
        for item in breakdowns:
            if not isinstance(item, dict):
                continue
            if item.get("modelName") != model:
                continue
            day = entry.get("date")
            cost = item.get("cost")
            if not isinstance(day, str) or not isinstance(cost, (int, float)):
                return day if isinstance(day, str) else None, None
            return day, float(cost)
    return None, None


def usd(value: float | None) -> str:
    if value is None:
        return "-"
    return f"${value:,.2f}"


def render_current_text(
    provider: str,
    model: str,
    latest_model_date: str | None,
    total_cost: float | None,
    latest_cost_date: str | None,
    latest_cost: float | None,
    row_count: int,
) -> str:
    lines = [
        f"Provider: {provider}",
        f"Current model: {model}",
        f"Total cost: {usd(total_cost)}",
        f"Daily rows: {row_count}",
    ]
    if latest_model_date:
        lines.append(f"Latest model date: {latest_model_date}")
    if latest_cost_date:
        lines.append(f"Latest day cost: {usd(latest_cost)} ({latest_cost_date})")
    return "\n".join(lines)


def render_all_text(provider: str, totals: dict[str, float]) -> str:
    lines = [f"Provider: {provider}", "Models:"]
    for model, cost in sorted(totals.items(), key=lambda row: row[1], reverse=True):
        lines.append(f"- {model}: {usd(cost)}")
    return "\n".join(lines)


def emit_output(payload: dict[str, Any], output_format: str, pretty: bool, json_out: str) -> None:
    if output_format == "json":
        indent = 2 if pretty else None
        text = json.dumps(payload, indent=indent, ensure_ascii=True, sort_keys=pretty)
        print(text)
    else:
        print(payload["_text"])

    if json_out:
        path = Path(json_out).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_payload = {k: v for k, v in payload.items() if not k.startswith("_")}
        path.write_text(json.dumps(file_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize local CodexBar model usage")
    parser.add_argument("--provider", choices=("codex", "claude"), default="codex")
    parser.add_argument("--mode", choices=("current", "all"), default="current")
    parser.add_argument("--model", default="", help="Explicit model override for current mode")
    parser.add_argument("--input", default="", help="JSON file path or '-' for stdin")
    parser.add_argument("--days", type=positive_int, default=None, help="Limit to last N days")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--json-out", default="", help="Optional JSON artifact path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_payload(args.input, args.provider)
        entries = filter_by_days(parse_daily_entries(payload), args.days)

        if args.mode == "current":
            model = args.model.strip()
            latest_model_date: str | None = None
            if not model:
                model, latest_model_date = pick_current_model(entries)
            if not model:
                raise RuntimeError("no model data found in payload")
            totals = aggregate_costs(entries)
            total_cost = totals.get(model)
            latest_cost_date, latest_cost = latest_day_cost(entries, model)
            out_payload: dict[str, Any] = {
                "provider": args.provider,
                "mode": "current",
                "model": model,
                "latest_model_date": latest_model_date,
                "total_cost_usd": total_cost,
                "latest_day_cost_usd": latest_cost,
                "latest_day_cost_date": latest_cost_date,
                "daily_row_count": len(entries),
            }
            out_payload["_text"] = render_current_text(
                provider=args.provider,
                model=model,
                latest_model_date=latest_model_date,
                total_cost=total_cost,
                latest_cost_date=latest_cost_date,
                latest_cost=latest_cost,
                row_count=len(entries),
            )
            emit_output(out_payload, args.format, args.pretty, args.json_out)
            return 0

        totals = aggregate_costs(entries)
        if not totals:
            raise RuntimeError("no model breakdowns found in payload")

        out_payload = {
            "provider": args.provider,
            "mode": "all",
            "models": [
                {"model": model, "total_cost_usd": cost}
                for model, cost in sorted(totals.items(), key=lambda row: row[1], reverse=True)
            ],
        }
        out_payload["_text"] = render_all_text(args.provider, totals)
        emit_output(out_payload, args.format, args.pretty, args.json_out)
        return 0
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
