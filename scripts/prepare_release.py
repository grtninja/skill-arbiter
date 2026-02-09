#!/usr/bin/env python3
"""Bump project version and prepend a changelog entry."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

PROJECT_FILE = Path("pyproject.toml")
CHANGELOG_FILE = Path("CHANGELOG.md")
DEFAULT_CHANGELOG_HEADER = (
    "# Changelog\n\n"
    "All notable changes to this project are documented in this file.\n"
)
VERSION_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$', re.MULTILINE)
CHANGELOG_ENTRY_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}\s*$", re.MULTILINE)


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run one subprocess and capture output."""

    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Prepare a release bump and changelog entry")
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        default="patch",
        help="Semantic version part to bump (ignored when --version is set)",
    )
    parser.add_argument(
        "--version",
        default="",
        help="Explicit semantic version (for example: 1.2.3)",
    )
    parser.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="Entry date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--max-notes",
        type=int,
        default=8,
        help="Maximum commit subjects to seed changelog notes with",
    )
    return parser.parse_args()


def read_current_version(pyproject_path: Path) -> tuple[str, tuple[int, int, int], str]:
    """Return current version string, parsed tuple, and file text."""

    text = pyproject_path.read_text(encoding="utf-8")
    match = VERSION_RE.search(text)
    if not match:
        raise ValueError(f"Could not find semantic version in {pyproject_path}")
    version_tuple = tuple(int(part) for part in match.groups())
    version = ".".join(match.groups())
    return version, version_tuple, text


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semantic version string."""

    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version!r}")
    return tuple(int(part) for part in match.groups())


def bump_version(current: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    """Return bumped semantic version tuple."""

    major, minor, patch = current
    if part == "major":
        return major + 1, 0, 0
    if part == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def render_updated_version(source_text: str, new_version: str) -> str:
    """Return pyproject content with first project version assignment replaced."""

    updated, replacements = VERSION_RE.subn(f'version = "{new_version}"', source_text, count=1)
    if replacements != 1:
        raise ValueError("Expected exactly one version field in pyproject.toml")
    return updated


def latest_git_tag() -> str:
    """Return latest reachable git tag or empty string when none exists."""

    result = run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def collect_commit_subjects(tag: str, max_notes: int) -> list[str]:
    """Collect unique commit subjects to seed changelog notes."""

    if max_notes < 1:
        return []
    if tag:
        cmd = ["git", "log", "--no-merges", "--pretty=format:%s", f"{tag}..HEAD"]
    else:
        cmd = ["git", "log", "--no-merges", "--pretty=format:%s", "-n", str(max_notes)]
    result = run(cmd, check=False)
    if result.returncode != 0:
        return []
    seen: set[str] = set()
    notes: list[str] = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line in seen:
            continue
        seen.add(line)
        notes.append(line)
        if len(notes) >= max_notes:
            break
    return notes


def prepend_changelog_entry(changelog_path: Path, version: str, date_text: str, notes: list[str]) -> None:
    """Insert a new top changelog entry for the given version."""

    if changelog_path.is_file():
        text = changelog_path.read_text(encoding="utf-8")
    else:
        text = DEFAULT_CHANGELOG_HEADER
    if re.search(rf"^## \[{re.escape(version)}\] - ", text, flags=re.MULTILINE):
        raise ValueError(f"Changelog already contains version {version}")

    note_lines = notes if notes else ["Release notes to be completed."]
    entry_notes = "\n".join(f"- {item}" for item in note_lines)
    entry = f"## [{version}] - {date_text}\n\n### Changed\n\n{entry_notes}"

    first_release = CHANGELOG_ENTRY_RE.search(text)
    if first_release:
        prefix = text[: first_release.start()].rstrip()
        suffix = text[first_release.start() :].lstrip("\n")
        merged = f"{prefix}\n\n{entry}\n\n{suffix}\n"
    else:
        merged = f"{text.rstrip()}\n\n{entry}\n"
    changelog_path.write_text(merged, encoding="utf-8")


def main() -> int:
    """CLI entrypoint."""

    args = parse_args()
    try:
        dt.date.fromisoformat(args.date)
    except ValueError:
        print(f"error: invalid --date value: {args.date!r}", file=sys.stderr)
        return 2

    if not PROJECT_FILE.is_file():
        print(f"error: missing {PROJECT_FILE}", file=sys.stderr)
        return 2

    try:
        current_str, current_tuple, pyproject_text = read_current_version(PROJECT_FILE)
        target_tuple = parse_semver(args.version) if args.version else bump_version(current_tuple, args.part)
        if target_tuple <= current_tuple:
            raise ValueError(
                f"Target version must be greater than current version: {current_str} -> "
                f'{".".join(str(v) for v in target_tuple)}'
            )
        target_str = ".".join(str(v) for v in target_tuple)
        updated_pyproject_text = render_updated_version(pyproject_text, target_str)

        tag = latest_git_tag()
        notes = collect_commit_subjects(tag, args.max_notes)
        prepend_changelog_entry(CHANGELOG_FILE, target_str, args.date, notes)
        PROJECT_FILE.write_text(updated_pyproject_text, encoding="utf-8")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"version: {current_str} -> {target_str}")
    print(f"updated: {PROJECT_FILE} and {CHANGELOG_FILE}")
    if tag:
        print(f"notes source: commit subjects since {tag}")
    else:
        print("notes source: recent commit subjects (no tags found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
