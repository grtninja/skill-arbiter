#!/usr/bin/env python3
"""Enforce VRM round-trip thresholds from a JSON report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate VRM round-trip metrics")
    parser.add_argument("--report-json", required=True, help="Path to roundtrip report JSON")
    parser.add_argument("--max-rot-deg", type=float, default=0.5)
    parser.add_argument("--max-pos", type=float, default=0.001)
    parser.add_argument("--max-blend", type=float, default=0.02)
    return parser.parse_args()


def max_or_zero(values: list[float]) -> float:
    return max(values) if values else 0.0


def collect_entries(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list):
            return [x for x in payload["results"] if isinstance(x, dict)]
        return [payload]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


def check(entry: dict, args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    fixture = entry.get("fixture", "unknown")
    buckets = entry.get("buckets", {}) if isinstance(entry.get("buckets"), dict) else {}

    hum = buckets.get("humanoid", {}) if isinstance(buckets.get("humanoid"), dict) else {}
    expr = buckets.get("expressions", {}) if isinstance(buckets.get("expressions"), dict) else {}

    rot = float(hum.get("rest_rot_deg_max", hum.get("tpose_deg_max", 0.0)) or 0.0)
    pos = float(hum.get("rest_pos_max", 0.0) or 0.0)
    blend = float(expr.get("weight_rms", 0.0) or 0.0)
    name_parity = hum.get("name_parity", 1.0)
    expr_parity = expr.get("name_parity", 1.0)

    if rot > args.max_rot_deg:
        errors.append(f"{fixture}: rotation {rot} > {args.max_rot_deg}")
    if pos > args.max_pos:
        errors.append(f"{fixture}: position {pos} > {args.max_pos}")
    if blend > args.max_blend:
        errors.append(f"{fixture}: blend {blend} > {args.max_blend}")
    if float(name_parity) < 1.0:
        errors.append(f"{fixture}: humanoid name parity < 1.0")
    if float(expr_parity) < 1.0:
        errors.append(f"{fixture}: expression name parity < 1.0")

    return errors


def main() -> None:
    args = parse_args()
    report_path = Path(args.report_json).expanduser().resolve()
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    entries = collect_entries(payload)
    if not entries:
        raise SystemExit("No valid report entries found")

    failures: list[str] = []
    for entry in entries:
        failures.extend(check(entry, args))

    if failures:
        print("VRM round-trip gate: FAIL")
        for failure in failures:
            print("-", failure)
        raise SystemExit(1)

    print("VRM round-trip gate: PASS")


if __name__ == "__main__":
    main()
