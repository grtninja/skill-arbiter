#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.public_readiness import run_public_readiness_scan


def main() -> int:
    payload = run_public_readiness_scan()
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
