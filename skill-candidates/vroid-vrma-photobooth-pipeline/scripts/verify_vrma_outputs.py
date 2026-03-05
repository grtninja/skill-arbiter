#!/usr/bin/env python3
"""Validate VRMA batch outputs and extension marker coverage."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VRMA export outputs")
    parser.add_argument("--out-dir", required=True, help="VRMA output folder")
    parser.add_argument("--summary", default="", help="Optional summary TSV path")
    parser.add_argument("--marker", default="VRMC_vrm_animation", help="ASCII marker required in every .vrma")
    parser.add_argument("--json-out", default="", help="Optional JSON report output")
    return parser.parse_args()


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_summary(path: Path) -> tuple[int, int]:
    ok = 0
    failed = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            status = (row.get("status") or "").strip()
            if status == "ok":
                ok += 1
            elif status == "failed":
                failed += 1
    return ok, failed


def has_marker(path: Path, marker: bytes) -> bool:
    data = path.read_bytes()
    return data.find(marker) >= 0


def main() -> int:
    args = parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    summary_path = Path(args.summary).expanduser().resolve() if args.summary else (out_dir / "vrma_export_summary.tsv")

    if not out_dir.is_dir():
        print(f"error: output directory not found: {out_dir}", file=sys.stderr)
        return 2
    if not summary_path.is_file():
        print(f"error: summary TSV not found: {summary_path}", file=sys.stderr)
        return 2

    try:
        ok_count, failed_count = parse_summary(summary_path)
    except (OSError, csv.Error) as exc:
        print(f"error: failed to parse summary: {exc}", file=sys.stderr)
        return 1

    vrma_files = sorted(out_dir.glob("*.vrma"))
    marker = args.marker.encode("ascii", errors="strict")

    missing_marker: list[str] = []
    for path in vrma_files:
        try:
            if not has_marker(path, marker):
                missing_marker.append(path.name)
        except OSError:
            missing_marker.append(path.name)

    report = {
        "out_dir": str(out_dir),
        "summary_path": str(summary_path),
        "ok": ok_count,
        "failed": failed_count,
        "vrma_count": len(vrma_files),
        "marker": args.marker,
        "marker_missing_count": len(missing_marker),
        "marker_missing": missing_marker,
    }

    write_json(args.json_out, report)
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if failed_count > 0:
        return 1
    if ok_count != len(vrma_files):
        return 1
    if missing_marker:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
