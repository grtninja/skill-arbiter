#!/usr/bin/env python3
"""Detect and optionally remove generated artifact files before admission."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ARTIFACT_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

ARTIFACT_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
}

ARTIFACT_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}


@dataclass
class Finding:
    path: str
    kind: str


@dataclass
class Report:
    root: str
    apply: bool
    fail_on_found: bool
    findings: list[Finding]
    removed: list[str]
    errors: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan and clean generated artifact files")
    parser.add_argument(
        "root",
        help="Root directory to scan (for example: /path/to/local/skills)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Remove detected artifacts",
    )
    parser.add_argument(
        "--fail-on-found",
        action="store_true",
        help="Exit non-zero when artifacts are detected",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write JSON report",
    )
    return parser.parse_args()


def discover(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        base = Path(dirpath)

        for dirname in list(dirnames):
            if dirname in ARTIFACT_DIR_NAMES:
                match = base / dirname
                findings.append(Finding(path=str(match), kind="dir"))
                # Prune matched artifact directories for faster deterministic scans.
                dirnames.remove(dirname)

        for filename in filenames:
            match = base / filename
            if filename in ARTIFACT_FILE_NAMES:
                findings.append(Finding(path=str(match), kind="file"))
                continue
            if match.suffix in ARTIFACT_FILE_SUFFIXES:
                findings.append(Finding(path=str(match), kind="file"))
    return findings


def apply_cleanup(findings: list[Finding]) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    errors: list[str] = []

    ordered = sorted(findings, key=lambda item: len(item.path), reverse=True)
    for item in ordered:
        path = Path(item.path)
        if not path.exists():
            continue
        try:
            if item.kind == "dir":
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(str(path))
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return removed, errors


def write_json(path_text: str, report: Report) -> None:
    if not path_text:
        return
    out_path = Path(path_text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"error: root directory not found: {root}", file=sys.stderr)
        return 2

    findings = discover(root)
    removed: list[str] = []
    errors: list[str] = []

    if args.apply and findings:
        removed, errors = apply_cleanup(findings)

    report = Report(
        root=str(root),
        apply=args.apply,
        fail_on_found=args.fail_on_found,
        findings=findings,
        removed=removed,
        errors=errors,
    )
    write_json(args.json_out, report)

    if not findings:
        print(f"artifact-hygiene: clean ({root})")
        return 0

    print(f"artifact-hygiene: found {len(findings)} artifact(s) in {root}")
    for item in findings:
        print(f"{item.kind}:{item.path}")

    if args.apply:
        print(f"artifact-hygiene: removed {len(removed)} artifact(s)")
        for item in removed:
            print(f"removed:{item}")
        if errors:
            for item in errors:
                print(f"error:{item}", file=sys.stderr)
            return 1
        return 0

    if args.fail_on_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
