#!/usr/bin/env python3
"""Arbitrate Codex skills one-by-one and quarantine noisy entries."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from supply_chain_guard import scan_skill_dir_content, scan_skill_tree, summarize_findings

DEFAULT_SKILLS_HOME = Path.home() / ".codex" / "skills"
CURATED_PATH = Path("skills/.curated")
DEFAULT_REPO = "https://github.com/openai/skills.git"
MAX_ALLOWED_RG_LIMIT = 3
SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DEFAULT_IMMUTABLE_FILE = ".immutable.local"
THIRD_PARTY_SKILL_ROW_RE = re.compile(r"^\|\s*`(?P<skill>[^`]+)`\s*\|")


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
    baseline_samples: list[int] = field(default_factory=list)
    raw_samples: list[int] = field(default_factory=list)
    baseline_max: int = 0
    raw_max_rg: int = 0
    raw_persistent_nonzero: bool = False
    supply_chain_blocked: bool = False
    supply_chain_codes: list[str] = field(default_factory=list)


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


def normalize_samples(raw_samples: list[int], baseline_max: int) -> list[int]:
    """Normalize samples against baseline rg activity."""

    floor = max(baseline_max, 0)
    return [max(value - floor, 0) for value in raw_samples]


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


def require_non_symlink_path(path: Path, label: str) -> None:
    """Reject symlinked control files to prevent unintended writes."""

    if path.is_symlink():
        raise ValueError(f"{label} cannot be a symlink: {path}")


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


def install_local_skill(source_dir: Path, skills_home: Path, skill: str, dry_run: bool) -> None:
    """Install one local skill from a provided source directory."""

    require_valid_skill_name(skill)
    source_path = source_dir / skill
    if source_path.is_symlink():
        raise ValueError(f"Local skill path cannot be a symlink: {source_path}")
    src = source_path.resolve()
    if not src.is_dir():
        raise FileNotFoundError(f"Local skill not found: {src}")
    dst = (skills_home / skill).resolve()
    if dry_run:
        return
    # Keep in place when source and destination are identical.
    if src == dst:
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def resolve_source_skill_dir(*, source_dir: Path | None, repo_root: Path | None, skill: str) -> Path:
    """Resolve the candidate skill directory before installation."""

    require_valid_skill_name(skill)
    if source_dir is not None:
        source_path = source_dir / skill
        if source_path.is_symlink():
            raise ValueError(f"Local skill path cannot be a symlink: {source_path}")
        return source_path.resolve()
    if repo_root is None:
        raise RuntimeError("Internal error: missing cloned repository")
    return (repo_root / CURATED_PATH / skill).resolve()


def is_repo_owned_source_dir(source_dir: Path | None) -> bool:
    """Return True only for repo-local candidate roots, not arbitrary external source dirs."""

    if source_dir is None:
        return False
    try:
        resolved = source_dir.resolve()
        candidate_root = (Path.cwd() / "skill-candidates").resolve()
        resolved.relative_to(candidate_root)
        return True
    except (OSError, ValueError):
        return False


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


def write_name_file(path: Path, names: set[str], dry_run: bool) -> None:
    """Write one-name-per-line file content."""

    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(f"{name}\n" for name in sorted(names))
    path.write_text(payload, encoding="utf-8")


def load_name_file(path: Path) -> set[str]:
    """Load one-name-per-line file content when present."""

    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def clone_repo(url: str) -> Path:
    """Clone skills repository and return the cloned repo path."""

    tmp_dir = Path(tempfile.mkdtemp(prefix="skill-arbiter-"))
    repo_root = tmp_dir / "repo"
    run(["git", "clone", "--depth", "1", url, str(repo_root)])
    return repo_root


def load_third_party_skill_names(source_dir: Path | None) -> set[str]:
    """Load attributed third-party skill names for a local candidate overlay."""

    if source_dir is None:
        return set()
    attribution_path = source_dir.parent / "references" / "third-party-skill-attribution.md"
    if not attribution_path.is_file():
        return set()
    names: set[str] = set()
    for line in attribution_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = THIRD_PARTY_SKILL_ROW_RE.match(line.strip())
        if match:
            names.add(match.group("skill").strip())
    return names


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Arbitrate curated skills for runaway rg.exe churn")
    parser.add_argument("skills", nargs="+", help="Curated skill names to test")
    parser.add_argument("--window", type=int, default=10, help="Sampling window in seconds")
    parser.add_argument(
        "--baseline-window",
        type=int,
        default=3,
        help="Baseline sampling window before each install (seconds)",
    )
    parser.add_argument("--threshold", type=int, default=3, help="Consecutive non-zero threshold")
    parser.add_argument(
        "--max-rg",
        type=int,
        default=MAX_ALLOWED_RG_LIMIT,
        help=(
            "Remove skill if any delta sample (raw - baseline_max) >= max-rg "
            f"(must be 1-{MAX_ALLOWED_RG_LIMIT})"
        ),
    )
    parser.add_argument("--json-out", default="", help="Optional path for machine-readable summary")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Git repository containing curated skills")
    parser.add_argument(
        "--source-dir",
        default="",
        help="Optional local skill source directory; when set, skips repo clone and installs <source-dir>/<skill>",
    )
    parser.add_argument("--dest", default=str(DEFAULT_SKILLS_HOME), help="Destination skills home")
    parser.add_argument("--blacklist", default=".blacklist.local", help="Blacklist filename under dest")
    parser.add_argument("--whitelist", default=".whitelist.local", help="Whitelist filename under dest")
    parser.add_argument(
        "--immutable",
        default=DEFAULT_IMMUTABLE_FILE,
        help="Immutable filename under dest; listed skills are never removed or blacklisted",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report actions without modifying files")
    parser.add_argument(
        "--promote-safe",
        action="store_true",
        help="When a skill passes arbitration, add it to whitelist and immutable files",
    )
    parser.add_argument(
        "--personal-lockdown",
        action="store_true",
        help="Personal mode: require --source-dir, force promote-safe, and harden local control paths",
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
        require_valid_blacklist_name(args.whitelist)
        require_valid_blacklist_name(args.immutable)
        if args.personal_lockdown and not args.source_dir:
            raise ValueError("--personal-lockdown requires --source-dir")
        if args.blacklist == args.whitelist:
            raise ValueError("--blacklist and --whitelist must be different files")
        if args.immutable in {args.blacklist, args.whitelist}:
            raise ValueError("--immutable must be different from --blacklist/--whitelist")
        if args.max_rg < 1 or args.max_rg > MAX_ALLOWED_RG_LIMIT:
            raise ValueError(f"--max-rg must be between 1 and {MAX_ALLOWED_RG_LIMIT}")
        if args.threshold < 1:
            raise ValueError("--threshold must be >= 1")
        if args.window < 1:
            raise ValueError("--window must be >= 1")
        if args.baseline_window < 1:
            raise ValueError("--baseline-window must be >= 1")
        normalized_skills = normalize_skills(args.skills)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    blacklist_path = skills_home / args.blacklist
    whitelist_path = skills_home / args.whitelist
    immutable_path = skills_home / args.immutable
    try:
        require_non_symlink_path(blacklist_path, "Blacklist file")
        require_non_symlink_path(whitelist_path, "Whitelist file")
        require_non_symlink_path(immutable_path, "Immutable file")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # In personal mode, always pin passing local skills.
    if args.personal_lockdown:
        args.promote_safe = True

    blacklist = load_name_file(blacklist_path)
    whitelist = load_name_file(whitelist_path)
    immutable: set[str] = set()
    for name in load_name_file(immutable_path):
        try:
            require_valid_skill_name(name)
        except ValueError:
            print(f"warning: ignored invalid immutable entry: {name!r}", file=sys.stderr)
            continue
        immutable.add(name)
    overlap = blacklist & whitelist
    if overlap:
        # Safety rail: conflicting entries should stay restricted by default.
        whitelist -= overlap
        print(
            f"warning: ignored {len(overlap)} whitelist entries that are blacklisted",
            file=sys.stderr,
        )
    immutable_blacklisted = immutable & blacklist
    if immutable_blacklisted:
        blacklist -= immutable_blacklisted
        print(
            f"warning: ignored {len(immutable_blacklisted)} blacklist entries that are immutable",
            file=sys.stderr,
        )
    results: list[ArbitrationResult] = []
    source_dir = Path(args.source_dir).expanduser().resolve() if args.source_dir else None
    if source_dir and not source_dir.is_dir():
        print(f"error: --source-dir does not exist: {source_dir}", file=sys.stderr)
        return 2
    third_party_skill_names = load_third_party_skill_names(source_dir)
    repo_root = clone_repo(args.repo) if not source_dir else None
    try:
        for skill in normalized_skills:
            if skill in immutable:
                results.append(
                    ArbitrationResult(
                        skill=skill,
                        installed=(skills_home / skill).is_dir(),
                        samples=[],
                        max_rg=0,
                        persistent_nonzero=False,
                        action="kept",
                        note="immutable locally; never removed/blacklisted",
                    )
                )
                continue
            # Local whitelist always wins: keep approved skills installed and skip arbitration.
            if skill in whitelist:
                note = "whitelisted locally; skipped arbitration"
                if args.personal_lockdown:
                    immutable.add(skill)
                    note = "whitelisted locally; pinned immutable via personal-lockdown"
                results.append(
                    ArbitrationResult(
                        skill=skill,
                        installed=(skills_home / skill).is_dir(),
                        samples=[],
                        max_rg=0,
                        persistent_nonzero=False,
                        action="kept",
                        note=note,
                    )
                )
                continue
            if skill in blacklist:
                remove_skill(skills_home, skill, args.dry_run)
                if not args.dry_run:
                    kill_rg_windows()
                results.append(
                    ArbitrationResult(
                        skill=skill,
                        installed=False,
                        samples=[],
                        max_rg=0,
                        persistent_nonzero=False,
                        action="deleted",
                        note="already blacklisted; permanently deleted",
                    )
                )
                continue
            try:
                source_skill_dir = resolve_source_skill_dir(
                    source_dir=source_dir,
                    repo_root=repo_root,
                    skill=skill,
                )
                supply_chain_findings = scan_skill_dir_content(source_skill_dir)
                scan_root = source_dir if source_dir is not None else repo_root
                if scan_root is not None:
                    supply_chain_findings.extend(scan_skill_tree(source_skill_dir, scan_root))
                supply_chain_summary = summarize_findings(supply_chain_findings)
                supply_chain_codes = list(dict.fromkeys(supply_chain_summary["codes"]))
                is_repo_owned_candidate = bool(
                    source_dir is not None
                    and is_repo_owned_source_dir(source_dir)
                    and skill not in third_party_skill_names
                )
                if (
                    not is_repo_owned_candidate
                    and (
                        supply_chain_summary["blocker_count"] > 0
                        or supply_chain_summary["warning_count"] > 0
                    )
                ):
                    remove_skill(skills_home, skill, args.dry_run)
                    if not args.dry_run:
                        kill_rg_windows()
                    blacklist.add(skill)
                    whitelist.discard(skill)
                    results.append(
                        ArbitrationResult(
                            skill=skill,
                            installed=False,
                            samples=[],
                            max_rg=0,
                            persistent_nonzero=False,
                            action="deleted",
                            note=(
                                "blocked by supply-chain guard: "
                                f"{','.join(supply_chain_codes) or 'unspecified'}"
                            ),
                            supply_chain_blocked=True,
                            supply_chain_codes=supply_chain_codes,
                        )
                    )
                    continue
                if not args.dry_run:
                    kill_rg_windows()
                baseline_samples = sample_counter(args.baseline_window)
                baseline_max = max(baseline_samples) if baseline_samples else 0
                if source_dir:
                    install_local_skill(source_dir, skills_home, skill, args.dry_run)
                else:
                    if repo_root is None:
                        raise RuntimeError("Internal error: missing cloned repository")
                    install_curated_skill(repo_root, skills_home, skill, args.dry_run)
            except (FileNotFoundError, ValueError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            raw_samples = sample_counter(args.window)
            samples = normalize_samples(raw_samples, baseline_max)
            max_rg = max(samples) if samples else 0
            raw_max_rg = max(raw_samples) if raw_samples else 0
            persistent = has_persistent_nonzero(samples, max(args.threshold, 1))
            raw_persistent = has_persistent_nonzero(raw_samples, max(args.threshold, 1))
            should_remove = persistent or (max_rg >= args.max_rg)
            sample_note = f"baseline_max={baseline_max};raw_max={raw_max_rg};delta_max={max_rg}"
            if should_remove:
                if skill in immutable:
                    action = "kept"
                    note = f"immutable locally; removal skipped ({sample_note})"
                else:
                    remove_skill(skills_home, skill, args.dry_run)
                    if not args.dry_run:
                        kill_rg_windows()
                    blacklist.add(skill)
                    whitelist.discard(skill)
                    action = "deleted"
                    note = f"blacklisted due to rg churn; permanently deleted ({sample_note})"
            else:
                action = "kept"
                note = f"delta within guardrail ({sample_note})"
                if args.promote_safe:
                    whitelist.add(skill)
                    immutable.add(skill)
                    note = f"promoted to whitelist+immutable ({sample_note})"
                    if args.personal_lockdown:
                        note = f"promoted to whitelist+immutable (personal-lockdown) ({sample_note})"
                    if supply_chain_codes and is_repo_owned_candidate:
                        note = (
                            "promoted to whitelist+immutable (personal-lockdown; repo-owned "
                            f"supply-chain codes={','.join(supply_chain_codes)}) ({sample_note})"
                        )
                elif source_dir is None:
                    # Third-party candidates are deny-by-default unless explicitly promoted.
                    remove_skill(skills_home, skill, args.dry_run)
                    action = "deleted"
                    note = f"passed arbitration but not promoted; third-party default deny ({sample_note})"
            results.append(
                ArbitrationResult(
                    skill=skill,
                    installed=True,
                    samples=samples,
                    max_rg=max_rg,
                    persistent_nonzero=persistent,
                    action=action,
                    note=note,
                    baseline_samples=baseline_samples,
                    raw_samples=raw_samples,
                    baseline_max=baseline_max,
                    raw_max_rg=raw_max_rg,
                    raw_persistent_nonzero=raw_persistent,
                    supply_chain_codes=supply_chain_codes,
                )
            )
    finally:
        if repo_root is not None:
            shutil.rmtree(repo_root.parent, ignore_errors=True)

    write_name_file(blacklist_path, blacklist, args.dry_run)
    write_name_file(whitelist_path, whitelist, args.dry_run)
    write_name_file(immutable_path, immutable, args.dry_run)

    payload = {
        "maintainer_alias": "grtninja",
        "license": "MIT",
        "skill": "skill-arbiter",
        "sampling_mode": "baseline-normalized-delta",
        "baseline_window": int(args.baseline_window),
        "dry_run": bool(args.dry_run),
        "results": [asdict(row) for row in results],
        "blacklist": sorted(blacklist),
        "whitelist": sorted(whitelist),
        "immutable": sorted(immutable),
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
