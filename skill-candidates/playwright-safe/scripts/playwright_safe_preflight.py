#!/usr/bin/env python3
"""Validate no-assets policy and basic Playwright runtime availability."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DISALLOWED_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg", ".gif", ".ico"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight checks for playwright-safe skill")
    parser.add_argument(
        "--skill-root",
        default=".",
        help="Skill root path to validate",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional JSON report path",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    out = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode, out


def find_disallowed_files(root: Path) -> list[str]:
    found: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in DISALLOWED_SUFFIXES:
            found.append(path.relative_to(root).as_posix())
    return sorted(found)


def main() -> int:
    args = parse_args()
    root = Path(args.skill_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: --skill-root is not a directory: {root}", file=sys.stderr)
        return 2

    assets_dir = root / "assets"
    has_assets_dir = assets_dir.is_dir()
    disallowed = find_disallowed_files(root)

    runtime_checks: list[dict[str, object]] = []
    overall_runtime_ok = False
    for cmd in (["playwright", "--version"], ["npx", "playwright", "--version"]):
        exe = shutil.which(cmd[0])
        if exe is None:
            runtime_checks.append(
                {
                    "cmd": cmd,
                    "available": False,
                    "exit_code": None,
                    "output": f"{cmd[0]} not found in PATH",
                }
            )
            continue
        code, out = run_cmd(cmd)
        ok = code == 0
        overall_runtime_ok = overall_runtime_ok or ok
        runtime_checks.append(
            {
                "cmd": cmd,
                "available": True,
                "exit_code": code,
                "output": out,
            }
        )

    policy_ok = (not has_assets_dir) and (not disallowed)
    payload = {
        "skill_root": str(root),
        "policy_ok": policy_ok,
        "has_assets_dir": has_assets_dir,
        "disallowed_files": disallowed,
        "runtime_ok": overall_runtime_ok,
        "runtime_checks": runtime_checks,
    }

    if args.json_out:
        Path(args.json_out).expanduser().write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    if not policy_ok:
        print("playwright-safe-preflight: failed policy checks")
        if has_assets_dir:
            print("error: assets/ directory is not allowed")
        if disallowed:
            print("error: disallowed image/icon files found:")
            for item in disallowed:
                print(f"  - {item}")
        return 1

    if overall_runtime_ok:
        print("playwright-safe-preflight: passed (policy+runtime)")
    else:
        print("playwright-safe-preflight: passed policy, runtime unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
