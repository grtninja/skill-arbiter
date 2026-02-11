#!/usr/bin/env python3
"""Validate local-first constraints for workspace tooling, URLs, and hardware checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
HTTP_SCHEMES = {"http", "https"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local compute preflight checks")
    parser.add_argument("--workspace-root", default=".", help="Workspace root path")
    parser.add_argument("--url", action="append", default=[], help="Service URL to validate (repeatable)")
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Additional exact host value allowed as local-equivalent",
    )
    parser.add_argument(
        "--allow-host-suffix",
        action="append",
        default=[],
        help="Additional host suffix allowed as local-equivalent (example: .local)",
    )
    parser.add_argument(
        "--require-vscode",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require VS Code CLI availability and a successful `code --version` call",
    )
    parser.add_argument(
        "--probe-http",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Probe HTTP/HTTPS URLs with a lightweight GET request",
    )
    parser.add_argument(
        "--strict-probe",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail when --probe-http is enabled and any probe fails",
    )
    parser.add_argument("--timeout-seconds", type=float, default=3.0, help="HTTP probe timeout in seconds")
    parser.add_argument(
        "--hardware-check",
        action="append",
        default=[],
        help='Hardware command to run (repeatable), example: "acclBench --hello"',
    )
    parser.add_argument(
        "--hardware-timeout-seconds",
        type=float,
        default=20.0,
        help="Timeout per hardware command",
    )
    parser.add_argument(
        "--strict-hardware",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail when any hardware check command fails",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def run_cmd(cmd: list[str], timeout_seconds: float | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = (proc.stdout or proc.stderr or "").strip()
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout_seconds}s"


def is_local_host(host: str, allowed: set[str], suffixes: list[str]) -> bool:
    if host in allowed:
        return True
    for suffix in suffixes:
        if host.endswith(suffix):
            return True
    return False


def normalize_suffixes(raw_suffixes: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_suffixes:
        text = str(raw or "").strip().lower()
        if not text:
            continue
        if not text.startswith("."):
            text = "." + text
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def normalize_hosts(raw_hosts: list[str]) -> set[str]:
    out = set(DEFAULT_ALLOWED_HOSTS)
    for raw in raw_hosts:
        text = str(raw or "").strip().lower()
        if text:
            out.add(text)
    return out


def validate_urls(
    urls: list[str],
    allowed_hosts: set[str],
    allowed_suffixes: list[str],
    probe_http: bool,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in urls:
        text = str(raw or "").strip()
        parsed = urlparse(text)
        host = (parsed.hostname or "").strip().lower()
        scheme = (parsed.scheme or "").strip().lower()
        local_ok = bool(host) and is_local_host(host, allowed_hosts, allowed_suffixes)
        row: dict[str, Any] = {
            "url": text,
            "scheme": scheme,
            "host": host,
            "local_ok": local_ok,
            "probe": None,
        }

        if probe_http and local_ok and scheme in HTTP_SCHEMES:
            req = Request(text, method="GET")
            try:
                with urlopen(req, timeout=timeout_seconds) as resp:  # nosec B310
                    row["probe"] = {
                        "ok": True,
                        "status": int(getattr(resp, "status", 0) or 0),
                        "error": "",
                    }
            except Exception as exc:  # pragma: no cover - environment dependent
                row["probe"] = {
                    "ok": False,
                    "status": 0,
                    "error": str(exc),
                }

        rows.append(row)
    return rows


def run_hardware_checks(raw_commands: list[str], timeout_seconds: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_commands:
        command = str(raw or "").strip()
        argv = shlex.split(command)
        if not argv:
            continue
        exe = argv[0]
        path = shutil.which(exe)
        if path is None:
            rows.append(
                {
                    "command": command,
                    "argv": argv,
                    "available": False,
                    "exit_code": None,
                    "ok": False,
                    "output": f"{exe} not found in PATH",
                }
            )
            continue

        exit_code, out = run_cmd(argv, timeout_seconds=timeout_seconds)
        rows.append(
            {
                "command": command,
                "argv": argv,
                "available": True,
                "exit_code": exit_code,
                "ok": exit_code == 0,
                "output": out.splitlines()[0] if out else "",
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    workspace_root = Path(args.workspace_root).expanduser().resolve()
    if not workspace_root.is_dir():
        print(f"error: --workspace-root is not a directory: {workspace_root}", file=sys.stderr)
        return 2

    code_check: dict[str, Any] = {
        "required": bool(args.require_vscode),
        "available": False,
        "exit_code": None,
        "output": "",
    }
    code_exe = shutil.which("code")
    if code_exe:
        exit_code, out = run_cmd(["code", "--version"])
        code_check["available"] = exit_code == 0
        code_check["exit_code"] = exit_code
        code_check["output"] = out.splitlines()[0] if out else ""
    else:
        code_check["available"] = False
        code_check["exit_code"] = None
        code_check["output"] = "code CLI not found in PATH"

    allowed_hosts = normalize_hosts(args.allow_host)
    allowed_suffixes = normalize_suffixes(args.allow_host_suffix)
    url_rows = validate_urls(
        urls=args.url,
        allowed_hosts=allowed_hosts,
        allowed_suffixes=allowed_suffixes,
        probe_http=bool(args.probe_http),
        timeout_seconds=float(args.timeout_seconds),
    )
    hardware_rows = run_hardware_checks(
        raw_commands=args.hardware_check,
        timeout_seconds=float(args.hardware_timeout_seconds),
    )

    non_local = [row for row in url_rows if not row.get("local_ok")]
    probe_failures = [
        row
        for row in url_rows
        if isinstance(row.get("probe"), dict) and not bool(row["probe"].get("ok"))
    ]
    hardware_failures = [row for row in hardware_rows if not bool(row.get("ok"))]

    failures: list[str] = []
    if args.require_vscode and not code_check["available"]:
        failures.append("vscode_cli_unavailable")
    if non_local:
        failures.append("non_local_hosts_detected")
    if args.probe_http and args.strict_probe and probe_failures:
        failures.append("endpoint_probe_failed")
    if args.strict_hardware and hardware_failures:
        failures.append("hardware_check_failed")

    payload: dict[str, Any] = {
        "workspace_root": str(workspace_root),
        "vscode": code_check,
        "allowed_hosts": sorted(allowed_hosts),
        "allowed_host_suffixes": allowed_suffixes,
        "urls": url_rows,
        "hardware_checks": hardware_rows,
        "summary": {
            "url_count": len(url_rows),
            "non_local_count": len(non_local),
            "probe_failures": len(probe_failures),
            "hardware_checks": len(hardware_rows),
            "hardware_failures": len(hardware_failures),
            "failures": failures,
            "pass": not failures,
        },
    }

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if failures:
        print("local-compute-preflight: failed")
        for item in failures:
            print(f"error: {item}")
        if non_local:
            print("non-local URLs:")
            for row in non_local:
                print(f"  - {row['url']} (host={row['host']})")
        if hardware_failures:
            print("hardware checks failed:")
            for row in hardware_failures:
                print(f"  - {row['command']} -> {row['output']}")
        return 1

    print("local-compute-preflight: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
