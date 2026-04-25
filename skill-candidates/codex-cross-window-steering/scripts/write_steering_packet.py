#!/usr/bin/env python3
"""Write a durable steering packet for another live Codex lane."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys


DEFAULT_OUT_DIR = Path("%USERPROFILE%/.codex/workstreams")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:80] or "codex-steering"


def _section(title: str, items: list[str]) -> str:
    if not items:
        return f"## {title}\n\n- none recorded\n"
    lines = [f"## {title}", ""]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines) + "\n"


def _set_clipboard(text: str) -> bool:
    candidates = [
        Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"),
        Path("/mnt/c/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe"),
    ]
    for exe in candidates:
        if not exe.exists():
            continue
        completed = subprocess.run(
            [str(exe), "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
            input=text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        if completed.returncode == 0:
            return True
    return False


def build_packet(args: argparse.Namespace) -> str:
    generated = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    parts = [
        f"# {args.title}",
        "",
        f"Generated: {generated}",
        f"Target lane: {args.target}",
        "",
        "## Steering Instruction",
        "",
        args.instruction.strip(),
        "",
        _section("Confirmed Evidence", args.confirmed),
        _section("Inferred Evidence", args.inferred),
        _section("Degraded Evidence", args.degraded),
        _section("Blocked Evidence", args.blocked),
        _section("Do Now", args.do),
        _section("Do Not Do", args.dont),
        _section("Artifacts And Commands", args.artifact),
        "## Acceptance Condition",
        "",
        args.acceptance.strip() if args.acceptance else "The target Codex lane acknowledges the packet or Eddie confirms it was pasted.",
        "",
    ]
    return "\n".join(parts)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--confirmed", action="append", default=[])
    parser.add_argument("--inferred", action="append", default=[])
    parser.add_argument("--degraded", action="append", default=[])
    parser.add_argument("--blocked", action="append", default=[])
    parser.add_argument("--do", action="append", default=[])
    parser.add_argument("--dont", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--acceptance", default="")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--clipboard", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    text = build_packet(args)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{_slug(args.title)}-{timestamp}.md"
    out_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"packet_path: {out_path}")
    if args.clipboard:
        print(f"clipboard_set: {_set_clipboard(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
