#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.agent_server import run_agent
from skill_arbiter.paths import DEFAULT_AGENT_HOST, DEFAULT_AGENT_PORT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NullClaw local arbitration agent")
    parser.add_argument("--host", default=DEFAULT_AGENT_HOST, help="Loopback host")
    parser.add_argument("--port", type=int, default=DEFAULT_AGENT_PORT, help="Loopback port")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_agent(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
