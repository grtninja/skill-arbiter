#!/usr/bin/env python3
"""Windows-started Skill Arbiter process babysitter.

This guard is intentionally small: it enforces the SQLite process policy DB and
keeps bounded tools like rg.exe from turning into CPU-saturating agent churn.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.process_policy_db import ensure_initialized, enforce_denied_processes, status


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enforce Skill Arbiter process policy from Windows startup")
    parser.add_argument("--once", action="store_true", help="Run one enforcement pass and exit")
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--json-out", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    db_path = ensure_initialized()
    passes = 0
    last_payload: dict = {}
    while True:
        passes += 1
        enforcement = enforce_denied_processes(dry_run=bool(args.dry_run), path=db_path)
        last_payload = {
            "generated_at_ms": int(time.time() * 1000),
            "database": str(db_path),
            "passes": passes,
            "dry_run": bool(args.dry_run),
            "enforcement": enforcement,
            "status": status(path=db_path),
        }
        if args.json_out:
            write_json(Path(args.json_out).expanduser(), last_payload)
        if args.once:
            print(json.dumps(last_payload, indent=2, ensure_ascii=True))
            return 0
        time.sleep(max(0.5, float(args.interval_seconds)))


if __name__ == "__main__":
    raise SystemExit(main())
