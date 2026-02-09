#!/usr/bin/env python3
"""Enforce release metadata updates for release-impacting pull requests."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_FILE = Path("pyproject.toml")
CHANGELOG_FILE = Path("CHANGELOG.md")
VERSION_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$', re.MULTILINE)
CHANGELOG_HEADING_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})\s*$")
NON_RELEASE_FILES = {
    ".gitattributes",
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE.txt",
    "README.md",
    "SECURITY-AUDIT.md",
    "SECURITY.md",
}
NON_RELEASE_PREFIXES = (".github/", "references/")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture output."""

    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    default_base = os.environ.get("GITHUB_BASE_REF", "main")
    parser = argparse.ArgumentParser(description="Check release hygiene for pull requests")
    parser.add_argument(
        "--base-ref",
        default=default_base,
        help=f"Base ref to compare against (default: {default_base!r})",
    )
    return parser.parse_args()


def ref_exists(ref: str) -> bool:
    """Return True when git can resolve a ref."""

    result = run(["git", "rev-parse", "--verify", "--quiet", ref], check=False)
    return result.returncode == 0


def resolve_base_ref(base_ref: str) -> str:
    """Resolve the preferred base ref name."""

    candidates = [f"origin/{base_ref}", base_ref]
    for candidate in candidates:
        if ref_exists(candidate):
            return candidate
    raise ValueError(
        f"Could not resolve base ref {base_ref!r}; expected one of: "
        f"{', '.join(candidates)}"
    )


def changed_files_since_merge_base(base_ref: str) -> tuple[str, list[str]]:
    """Return merge-base commit and changed files list."""

    merge_base = run(["git", "merge-base", "HEAD", base_ref]).stdout.strip()
    if not merge_base:
        raise ValueError(f"Could not compute merge-base for HEAD and {base_ref}")
    changed = run(["git", "diff", "--name-only", f"{merge_base}...HEAD"]).stdout.splitlines()
    files = [line.strip() for line in changed if line.strip()]
    return merge_base, files


def is_release_impacting(path: str) -> bool:
    """Return True when a changed file should require release metadata updates."""

    if path in NON_RELEASE_FILES:
        return False
    if any(path.startswith(prefix) for prefix in NON_RELEASE_PREFIXES):
        return False
    if path.endswith(".md") and path != "SKILL.md":
        return False
    return True


def parse_semver_from_text(text: str, context: str) -> tuple[int, int, int]:
    """Extract semantic version tuple from pyproject content."""

    match = VERSION_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse version from {context}")
    return tuple(int(part) for part in match.groups())


def parse_current_semver(project_file: Path) -> tuple[int, int, int]:
    """Parse semantic version from current working tree file."""

    if not project_file.is_file():
        raise ValueError(f"Missing {project_file}")
    return parse_semver_from_text(project_file.read_text(encoding="utf-8"), str(project_file))


def parse_base_semver(base_ref: str, project_file: Path) -> tuple[int, int, int]:
    """Parse semantic version from base branch tip."""

    result = run(["git", "show", f"{base_ref}:{project_file.as_posix()}"], check=False)
    if result.returncode != 0:
        raise ValueError(f"Could not read {project_file} from base ref {base_ref}")
    return parse_semver_from_text(result.stdout, f"{base_ref}:{project_file.as_posix()}")


def parse_latest_changelog_version(changelog_file: Path) -> str:
    """Return version from top changelog release heading."""

    if not changelog_file.is_file():
        raise ValueError(f"Missing {changelog_file}")
    for raw_line in changelog_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        match = CHANGELOG_HEADING_RE.match(line)
        if match:
            return match.group(1)
    raise ValueError(f"Could not parse a release heading from {changelog_file}")


def fmt_semver(value: tuple[int, int, int]) -> str:
    """Format semantic version tuple."""

    return ".".join(str(part) for part in value)


def main() -> int:
    """CLI entrypoint."""

    args = parse_args()
    errors: list[str] = []
    try:
        base_ref = resolve_base_ref(args.base_ref)
        merge_base, changed_files = changed_files_since_merge_base(base_ref)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    release_impacting = [path for path in changed_files if is_release_impacting(path)]
    if not release_impacting:
        print("release-hygiene: no release-impacting file changes detected")
        return 0

    required = {PROJECT_FILE.as_posix(), CHANGELOG_FILE.as_posix()}
    changed_set = set(changed_files)
    missing = sorted(path for path in required if path not in changed_set)
    for path in missing:
        errors.append(
            f"Missing required release update: {path} (release-impacting files changed)"
        )

    try:
        current_version = parse_current_semver(PROJECT_FILE)
        base_version = parse_base_semver(base_ref, PROJECT_FILE)
        if current_version <= base_version:
            errors.append(
                f"Version must increase for release-impacting changes: "
                f"{fmt_semver(base_version)} -> {fmt_semver(current_version)}"
            )
        latest_changelog_version = parse_latest_changelog_version(CHANGELOG_FILE)
        if latest_changelog_version != fmt_semver(current_version):
            errors.append(
                f"Top changelog entry must match pyproject version: "
                f"{latest_changelog_version} != {fmt_semver(current_version)}"
            )
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        print("release-hygiene: failed")
        print("release-hygiene: release-impacting files:")
        for path in release_impacting:
            print(f"  - {path}")
        for item in errors:
            print(f"error: {item}", file=sys.stderr)
        print(
            "hint: run `python3 scripts/prepare_release.py --part patch` and "
            "update CHANGELOG.md notes",
            file=sys.stderr,
        )
        return 1

    print("release-hygiene: passed")
    print(f"release-hygiene: base {fmt_semver(base_version)} -> head {fmt_semver(current_version)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
