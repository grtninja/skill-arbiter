#!/usr/bin/env python3
"""Compare two repo roots for Cybertron parity work."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import subprocess


@dataclass
class RepoState:
    root: str
    exists: bool
    git_root: bool
    branch: str = ""
    head: str = ""
    dirty: bool = False
    untracked: list[str] = field(default_factory=list)


@dataclass
class ParityReport:
    left: RepoState
    right: RepoState
    same_head: bool
    same_branch: bool
    same_dirty_state: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two repo roots for parity")
    parser.add_argument("--left", required=True, help="Left repo root")
    parser.add_argument("--right", required=True, help="Right repo root")
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def git_output(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def read_state(path_text: str) -> RepoState:
    root = Path(path_text).expanduser()
    exists = root.is_dir()
    git_root = exists and bool(git_output(root, "rev-parse", "--is-inside-work-tree"))
    state = RepoState(root=str(root), exists=exists, git_root=git_root, untracked=[])
    if not git_root:
        return state

    state.branch = git_output(root, "rev-parse", "--abbrev-ref", "HEAD")
    state.head = git_output(root, "rev-parse", "HEAD")
    status = git_output(root, "status", "--porcelain")
    lines = [line for line in status.splitlines() if line.strip()]
    state.dirty = bool(lines)
    state.untracked = [line[3:] for line in lines if line.startswith("?? ")]
    return state


def main() -> int:
    args = parse_args()
    left = read_state(args.left)
    right = read_state(args.right)
    report = ParityReport(
        left=left,
        right=right,
        same_head=bool(left.head and left.head == right.head),
        same_branch=bool(left.branch and left.branch == right.branch),
        same_dirty_state=left.dirty == right.dirty,
    )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if not left.exists or not right.exists:
        print("parity: missing one or both repo roots")
        return 2

    print(f"parity: left={left.root} right={right.root}")
    print(f"left-head={left.head or '<none>'}")
    print(f"right-head={right.head or '<none>'}")
    print(f"same-head={report.same_head}")
    print(f"same-branch={report.same_branch}")
    print(f"same-dirty-state={report.same_dirty_state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
