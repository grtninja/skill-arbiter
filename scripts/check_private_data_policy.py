#!/usr/bin/env python3
"""Fail when private identifiers or user-specific paths appear in tracked files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

USER_PATH_PATTERNS = (
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"/mnt/[A-Za-z]/Users/[A-Za-z0-9._ -]+/"),
    re.compile(r"[A-Za-z]:/Users/[A-Za-z0-9._ -]+/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._ -]+\\\\"),
)

SENSITIVE_TOKEN_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9][A-Za-z0-9-]*-Internal\b"),
    re.compile(r"\b[A-Za-z0-9]+---[A-Za-z0-9]+\b"),
    re.compile(r"\b[a-z0-9-]+-python-shim\b", re.IGNORECASE),
    re.compile(r"\b[A-Z][A-Za-z0-9-]*-Sandbox\b"),
    re.compile(r"GitHub[\\\\/](?!<)[A-Za-z0-9._-]+"),
)

ROOT_HINT_RE = re.compile(r"Run from `([^`]+)` root:")
REPO_TOKEN_RE = re.compile(r"[A-Za-z0-9]+-[A-Za-z0-9-]+")


@dataclass
class Violation:
    path: Path
    line: int
    col: int
    kind: str
    snippet: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check repository privacy policy")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Scan only staged files (for git pre-commit hooks)",
    )
    return parser.parse_args()


def tracked_paths(staged: bool) -> list[Path]:
    if staged:
        output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"])
    else:
        output = run_git(["ls-files"])

    paths: list[Path] = []
    for raw in output.splitlines():
        path_text = raw.strip()
        if not path_text:
            continue
        path = Path(path_text)
        if path.is_file():
            paths.append(path)
    return paths


def is_binary(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\x00" in sample


def scan_text(path: Path, text: str) -> list[Violation]:
    findings: list[Violation] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        for pattern in USER_PATH_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    Violation(
                        path=path,
                        line=line_num,
                        col=match.start() + 1,
                        kind="user-absolute-path",
                        snippet=match.group(0),
                    )
                )
        for pattern in SENSITIVE_TOKEN_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    Violation(
                        path=path,
                        line=line_num,
                        col=match.start() + 1,
                        kind="private-repo-identifier",
                        snippet=match.group(0),
                    )
                )

        # Skill-candidate docs must use placeholder repo names.
        if path.as_posix().startswith("skill-candidates/") and path.name in {
            "SKILL.md",
            "openai.yaml",
        }:
            root_match = ROOT_HINT_RE.search(line)
            if root_match:
                target = root_match.group(1).strip()
                if not (
                    target.startswith("<")
                    or target.startswith("/path/")
                    or target.startswith("$")
                ):
                    findings.append(
                        Violation(
                            path=path,
                            line=line_num,
                            col=root_match.start(1) + 1,
                            kind="repo-placeholder-required",
                            snippet=target,
                        )
                    )

            if line.startswith("description:") and " in " in line and "<" not in line:
                suffix = line.split(" in ", 1)[1]
                token_match = REPO_TOKEN_RE.search(suffix)
                if token_match:
                    token = token_match.group(0)
                    if token != "skill-arbiter":
                        findings.append(
                            Violation(
                                path=path,
                                line=line_num,
                                col=token_match.start() + line.find(suffix) + 1,
                                kind="repo-placeholder-required",
                                snippet=token,
                            )
                        )
    return findings


def scan_path(path: Path) -> list[Violation]:
    if is_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return scan_text(path, text)


def main() -> int:
    args = parse_args()
    try:
        paths = tracked_paths(args.staged)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings: list[Violation] = []
    for path in paths:
        findings.extend(scan_path(path))

    if findings:
        print("privacy-policy: failed")
        for item in findings:
            print(
                f"{item.path.as_posix()}:{item.line}:{item.col}: "
                f"{item.kind}: {item.snippet}",
                file=sys.stderr,
            )
        print(
            "hint: replace private repo names and user-specific absolute paths with placeholders.",
            file=sys.stderr,
        )
        return 1

    scope = "staged-files" if args.staged else "tracked-files"
    print(f"privacy-policy: passed ({scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
