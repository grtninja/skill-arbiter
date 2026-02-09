#!/usr/bin/env python3
"""Arbitrate Codex skills one-by-one and quarantine noisy entries.

MIT-licensed workflow authored by Edward Silvia.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_SKILLS_HOME = Path.home() / ".codex" / "skills"
CURATED_PATH = Path("skills/.curated")
DEFAULT_REPO = "https://github.com/openai/skills.git"
MAX_ALLOWED_RG_LIMIT = 3
SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass
class ArbitrationResult:
    """One skill arbitration result row."""

    skill: str
    installed: bool
    samples: list[int]
    max_rg: int
    persistent_nonzero: bool
    action: str
    note: str = ""


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and return completed process."""

    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def rg_count_windows() -> int:
    """Return current rg.exe process count on Windows hosts."""

    out = run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "(Get-Process rg -ErrorAction SilentlyContinue | Measure-Object).Count",
        ],
        check=False,
    ).stdout.strip()
    digits = "".join(ch for ch in out if ch.isdigit())
    return int(digits or "0")


def kill_rg_windows() -> None:
    """Kill rg.exe processes on Windows hosts."""

    run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            '$ErrorActionPreference="SilentlyContinue"; Get-Process rg | Stop-Process -Force',
        ],
        check=False,
    )


def sample_counter(window_s: int) -> list[int]:
    """Sample rg process count once per second for the requested window."""

    values: list[int] = []
    for _ in range(max(window_s, 1)):
        values.append(rg_count_windows())
        time.sleep(1)
    return values


def has_persistent_nonzero(samples: Iterable[int], threshold_s: int) -> bool:
    """Return True when nonzero samples persist for threshold duration."""

    streak = 0
    for value in samples:
        if value > 0:
            streak += 1
            if streak >= threshold_s:
                return True
        else:
            streak = 0
    return False


def require_valid_skill_name(name: str) -> None:
    """Enforce conservative skill names to block path traversal input."""

    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid skill name: {name!r}")


def require_valid_blacklist_name(name: str) -> None:
    """Require a file-name-like blacklist value under destination root."""

    candidate = Path(name)
    if candidate.is_absolute() or candidate.parent != Path("."):
        raise ValueError("Blacklist must be a filename under --dest")


def install_curated_skill(repo_root: Path, skills_home: Path, skill: str, dry_run: bool) -> None:
    """Install one curated skill into the destination skills directory."""

    require_valid_skill_name(skill)
    src = repo_root / CURATED_PATH / skill
    if not src.is_dir():
        raise FileNotFoundError(f"Curated skill not found: {src}")
    dst = skills_home / skill
    if dry_run:
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def remove_skill(skills_home: Path, skill: str, dry_run: bool) -> None:
    """Remove one installed skill."""

    require_valid_skill_name(skill)
    if dry_run:
        return
    dst = skills_home / skill
    if dst.exists():
        shutil.rmtree(dst)


def write_blacklist(path: Path, names: set[str], dry_run: bool) -> None:
    """Write blacklist file content."""

    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(f"{name}\n" for name in sorted(names))
    path.write_text(payload, encoding="utf-8")


def load_blacklist(path: Path) -> set[str]:
    """Load blacklist names from file when present."""

    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def clone_repo(url: str) -> Path:
    """Clone skills repository and return the cloned repo path."""

    tmp_dir = Path(tempfile.mkdtemp(prefix="skill-arbiter-"))
    repo_root = tmp_dir / "repo"
    run(["git", "clone", "--depth", "1", url, str(repo_root)])
    return repo_root


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Arbitrate curated skills for runaway rg.exe churn")
    parser.add_argument("skills", nargs="+", help="Curated skill names to test")
    parser.add_argument("--window", type=int, default=10, help="Sampling window in seconds")
    parser.add_argument("--threshold", type=int, default=3, help="Consecutive non-zero threshold")
    parser.add_argument(
        "--max-rg",
        type=int,
        default=MAX_ALLOWED_RG_LIMIT,
        help=f"Remove skill if any sample >= max-rg (must be 1-{MAX_ALLOWED_RG_LIMIT})",
    )
    parser.add_argument("--json-out", default="", help="Optional path for machine-readable summary")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Git repository containing curated skills")
    parser.add_argument("--dest", default=str(DEFAULT_SKILLS_HOME), help="Destination skills home")
    parser.add_argument("--blacklist", default=".blacklist.local", help="Blacklist filename under dest")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without modifying files")
    parser.add_argument(
        "--retest-blacklisted",
        action="store_true",
        help="Allow re-testing skills already on the local blacklist",
    )
    return parser.parse_args()


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """Normalize CLI skill list and reject empty entries."""

    skills: list[str] = []
    for skill in raw_skills:
        normalized = skill.strip()
        if not normalized:
            raise ValueError("Empty skill name is not allowed")
        require_valid_skill_name(normalized)
        skills.append(normalized)
    return skills


def main() -> int:
    """Run the arbitration workflow and print summary table."""

    args = parse_args()
    skills_home = Path(args.dest).expanduser().resolve()
    try:
        require_valid_blacklist_name(args.blacklist)
        if args.max_rg < 1 or args.max_rg > MAX_ALLOWED_RG_LIMIT:
            raise ValueError(f"--max-rg must be between 1 and {MAX_ALLOWED_RG_LIMIT}")
        if args.threshold < 1:
            raise ValueError("--threshold must be >= 1")
        if args.window < 1:
            raise ValueError("--window must be >= 1")
        normalized_skills = normalize_skills(args.skills)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    blacklist_path = skills_home / args.blacklist
    blacklist = load_blacklist(blacklist_path)
    results: list[ArbitrationResult] = []

    repo_root = clone_repo(args.repo)
    try:
        for skill in normalized_skills:
            if skill in blacklist and not args.retest_blacklisted:
                remove_skill(skills_home, skill, args.dry_run)
                results.append(
                    ArbitrationResult(
                        skill=skill,
                        installed=False,
                        samples=[],
                        max_rg=0,
                        persistent_nonzero=False,
                        action="restricted",
                        note="already blacklisted; off by default",
                    )
                )
                continue
            try:
                install_curated_skill(repo_root, skills_home, skill, args.dry_run)
            except (FileNotFoundError, ValueError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            samples = sample_counter(args.window)
            max_rg = max(samples) if samples else 0
            persistent = has_persistent_nonzero(samples, max(args.threshold, 1))
            should_remove = persistent or (max_rg >= args.max_rg)
            if should_remove:
                remove_skill(skills_home, skill, args.dry_run)
                if not args.dry_run:
                    kill_rg_windows()
                blacklist.add(skill)
                action = "removed"
                note = "blacklisted due to rg churn"
            else:
                action = "kept"
                note = ""
            results.append(
                ArbitrationResult(
                    skill=skill,
                    installed=True,
                    samples=samples,
                    max_rg=max_rg,
                    persistent_nonzero=persistent,
                    action=action,
                    note=note,
                )
            )
    finally:
        shutil.rmtree(repo_root.parent, ignore_errors=True)

    write_blacklist(blacklist_path, blacklist, args.dry_run)

    payload = {
        "author": "Edward Silvia",
        "license": "MIT",
        "skill": "skill-arbiter",
        "dry_run": bool(args.dry_run),
        "results": [asdict(row) for row in results],
        "blacklist": sorted(blacklist),
    }
    if args.json_out:
        Path(args.json_out).expanduser().write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    print("skill,installed,max_rg,persistent_nonzero,action,note")
    for row in results:
        print(
            f"{row.skill},{str(row.installed).lower()},{row.max_rg},"
            f"{str(row.persistent_nonzero).lower()},{row.action},{row.note}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
