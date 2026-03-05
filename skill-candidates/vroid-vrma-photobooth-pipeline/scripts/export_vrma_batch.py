#!/usr/bin/env python3
"""Run Unity batch export for VRoid Photo Booth clips into VRMA files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VroidVrmaBatch export in Unity")
    parser.add_argument("--unity-exe", required=True, help="Path to Unity.exe")
    parser.add_argument("--unity-project", required=True, help="Path to Unity project")
    parser.add_argument("--out-dir", required=True, help="Output directory for .vrma files")
    parser.add_argument(
        "--prefab",
        default="Assets/Resources/animations/female/unitychan_WAIT00.prefab",
        help="Avatar prefab asset path inside Unity project",
    )
    parser.add_argument(
        "--clip-roots",
        default="Assets/Resources/animations/female;Assets/Resources/animations/male;Assets/Resources/animations/pv/female;Assets/Resources/animations/pv/male",
        help="Semicolon-delimited AnimationClip search roots",
    )
    parser.add_argument("--name-filter", default="", help="Optional clip-path filter")
    parser.add_argument("--limit", type=int, default=0, help="Optional clip processing limit")
    parser.add_argument("--log-file", default="", help="Optional Unity log file path")
    parser.add_argument("--json-out", default="", help="Optional JSON report output")
    return parser.parse_args()


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_summary(summary_path: Path) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append({key: (value or "") for key, value in row.items()})

    ok_rows = [row for row in rows if row.get("status") == "ok"]
    failed_rows = [row for row in rows if row.get("status") == "failed"]
    return {
        "rows": rows,
        "ok": len(ok_rows),
        "failed": len(failed_rows),
    }


def main() -> int:
    args = parse_args()

    unity_exe = Path(args.unity_exe).expanduser().resolve()
    unity_project = Path(args.unity_project).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    log_file = Path(args.log_file).expanduser().resolve() if args.log_file else (out_dir / "unity_vrma_batch.log")

    if not unity_exe.is_file():
        print(f"error: unity exe not found: {unity_exe}", file=sys.stderr)
        return 2
    if not unity_project.is_dir():
        print(f"error: unity project not found: {unity_project}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(unity_exe),
        "-batchmode",
        "-quit",
        "-projectPath",
        str(unity_project),
        "-logFile",
        str(log_file),
        "-executeMethod",
        "VroidVrmaBatch.Run",
        f"--out-dir={out_dir}",
        f"--prefab={args.prefab}",
        f"--clip-roots={args.clip_roots}",
    ]
    if args.name_filter:
        cmd.append(f"--name-filter={args.name_filter}")
    if args.limit > 0:
        cmd.append(f"--limit={args.limit}")

    result = subprocess.run(cmd, check=False)

    summary_path = out_dir / "vrma_export_summary.tsv"
    report: dict[str, Any] = {
        "command": cmd,
        "return_code": int(result.returncode),
        "log_file": str(log_file),
        "out_dir": str(out_dir),
        "summary_path": str(summary_path),
        "ok": 0,
        "failed": 0,
    }

    if not summary_path.is_file():
        report["error"] = "summary file missing"
        write_json(args.json_out, report)
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 1

    try:
        parsed = parse_summary(summary_path)
    except (OSError, csv.Error) as exc:
        report["error"] = f"failed to parse summary: {exc}"
        write_json(args.json_out, report)
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 1

    report["ok"] = int(parsed["ok"])
    report["failed"] = int(parsed["failed"])

    write_json(args.json_out, report)
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if result.returncode != 0:
        return 1
    if report["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
