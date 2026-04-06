#!/usr/bin/env python3
"""Fail when governed repo surfaces include vendor review hooks or remote workflow actions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.external_review_hygiene import scan_repo
from skill_arbiter.paths import REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check external review hygiene in governed repo surfaces")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Scan only staged files (for git pre-commit hooks)",
    )
    parser.add_argument(
        "--base-ref",
        default="",
        help="Scan the git diff against this base ref instead of the whole tracked tree",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = scan_repo(REPO_ROOT, staged=args.staged, base_ref=args.base_ref)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not result.passed:
        print("external-review-hygiene: failed")
        for item in result.findings:
            print(
                f"{item.path}:{item.line}:{item.col}: "
                f"{item.kind}: {item.snippet}",
                file=sys.stderr,
            )
        print(
            "hint: keep vendor review tooling markers and remote workflow actions out of governed repo surfaces.",
            file=sys.stderr,
        )
        return 1

    print(f"external-review-hygiene: passed ({result.scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
