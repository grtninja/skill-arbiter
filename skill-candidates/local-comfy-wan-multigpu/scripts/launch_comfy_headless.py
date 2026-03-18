#!/usr/bin/env python3
"""Launch ComfyUI headlessly and wait for readiness."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch ComfyUI headlessly and wait for readiness")
    parser.add_argument("--python", type=Path, required=True, help="Interpreter to launch Comfy with")
    parser.add_argument("--main", type=Path, required=True, help="Path to Comfy main.py")
    parser.add_argument("--base-dir", type=Path, required=True, help="Comfy base directory")
    parser.add_argument("--user-dir", type=Path, required=True, help="Comfy user directory")
    parser.add_argument("--input-dir", type=Path, required=True, help="Comfy input directory")
    parser.add_argument("--output-dir", type=Path, required=True, help="Comfy output directory")
    parser.add_argument("--front-end-root", type=Path, required=True, help="Comfy frontend root")
    parser.add_argument("--extra-models-config", type=Path, required=True, help="Extra models config")
    parser.add_argument("--database-url", required=True, help="Comfy database URL")
    parser.add_argument("--host", default="127.0.0.1", help="Listen host")
    parser.add_argument("--port", type=int, default=8000, help="Listen port")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for readiness")
    parser.add_argument("--stdout-log", type=Path, required=True, help="Stdout log file")
    parser.add_argument("--stderr-log", type=Path, required=True, help="Stderr log file")
    parser.add_argument("--enable-manager", action="store_true", help="Pass --enable-manager")
    parser.add_argument(
        "--cuda-visible-devices",
        default="",
        help="Optional CUDA_VISIBLE_DEVICES mask for single-lane servers (for example: 0 or 1)",
    )
    return parser.parse_args()


def system_stats_ready(host: str, port: int) -> bool:
    try:
        with urlopen(f"http://{host}:{port}/system_stats", timeout=3) as response:
            return response.status == 200
    except URLError:
        return False
    except Exception:
        return False


def main() -> int:
    args = parse_args()
    args.stdout_log.parent.mkdir(parents=True, exist_ok=True)
    args.stderr_log.parent.mkdir(parents=True, exist_ok=True)

    argv = [
        str(args.main),
        "--user-directory",
        str(args.user_dir),
        "--input-directory",
        str(args.input_dir),
        "--output-directory",
        str(args.output_dir),
        "--front-end-root",
        str(args.front_end_root),
        "--base-directory",
        str(args.base_dir),
        "--database-url",
        args.database_url,
        "--extra-model-paths-config",
        str(args.extra_models_config),
        "--log-stdout",
        "--listen",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.enable_manager:
        argv.append("--enable-manager")

    env = None
    if args.cuda_visible_devices.strip():
        env = dict(os.environ)
        env["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices.strip()

    with args.stdout_log.open("wb") as stdout_handle, args.stderr_log.open("wb") as stderr_handle:
        proc = subprocess.Popen(
            [str(args.python), *argv],
            cwd=str(args.base_dir),
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )

    deadline = time.time() + max(args.timeout, 1)
    while time.time() < deadline:
        if system_stats_ready(args.host, args.port):
            print(proc.pid)
            return 0
        if proc.poll() is not None:
            print(f"comfy_exited pid={proc.pid} returncode={proc.returncode}", file=sys.stderr)
            return 1
        time.sleep(2)

    print(f"comfy_not_ready pid={proc.pid}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
