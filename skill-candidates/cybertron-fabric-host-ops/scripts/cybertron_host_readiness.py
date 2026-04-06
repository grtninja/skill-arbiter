#!/usr/bin/env python3
"""Check Cybertron readiness signals across network and local markers."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import socket
import sys
from urllib.error import URLError
from urllib.request import urlopen


@dataclass
class PortCheck:
    port: int
    state: str


@dataclass
class HostReadinessReport:
    host: str
    port_checks: list[PortCheck]
    public_model_plane: str
    hosted_27b_lane: str
    meshgpt: str
    vrm_display: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Cybertron readiness signals")
    parser.add_argument("--host", default="CYBERTRON_CORE", help="Host name or address")
    parser.add_argument(
        "--ports",
        nargs="+",
        type=int,
        default=[5985, 3389, 9000, 2337, 8892],
        help="Ports to probe",
    )
    parser.add_argument("--timeout", type=float, default=2.0, help="Socket timeout seconds")
    parser.add_argument(
        "--vrm-marker",
        default="",
        help="Optional file path that marks VRM display readiness",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless the required checks are ready",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def tcp_check(host: str, port: int, timeout: float) -> str:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "open"
    except OSError:
        return "closed"


def http_check(url: str, timeout: float) -> str:
    try:
        with urlopen(url, timeout=timeout) as response:
            if 200 <= response.status < 400:
                return f"ready:{response.status}"
            return f"blocked:{response.status}"
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return f"error:{reason}"
    except Exception as exc:  # pragma: no cover - defensive network path
        return f"error:{exc}"


def main() -> int:
    args = parse_args()
    host = args.host
    checks = [PortCheck(port=port, state=tcp_check(host, port, args.timeout)) for port in args.ports]
    public_model_plane = http_check(f"http://{host}:9000/v1/models", args.timeout) if 9000 in args.ports else "unknown"
    hosted_27b_lane = http_check(f"http://{host}:2337/v1/models", args.timeout) if 2337 in args.ports else "unknown"
    meshgpt = http_check(f"http://{host}:8892/health", args.timeout) if 8892 in args.ports else "unknown"
    if args.vrm_marker:
        vrm_marker = Path(args.vrm_marker).expanduser()
        vrm_display = "ready" if vrm_marker.is_file() else "blocked"
    else:
        vrm_display = "unknown"

    report = HostReadinessReport(
        host=host,
        port_checks=checks,
        public_model_plane=public_model_plane,
        hosted_27b_lane=hosted_27b_lane,
        meshgpt=meshgpt,
        vrm_display=vrm_display,
    )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"host={host}")
    for item in checks:
        print(f"port:{item.port}={item.state}")
    print(f"public_model_plane={public_model_plane}")
    print(f"hosted_27b_lane={hosted_27b_lane}")
    print(f"meshgpt={meshgpt}")
    print(f"vrm_display={vrm_display}")
    if args.require_ready:
        required_ok = all(item.state == "open" for item in checks if item.port in {5985, 9000, 2337, 8892})
        if args.vrm_marker:
            required_ok = required_ok and vrm_display == "ready"
        return 0 if required_ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
