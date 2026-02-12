#!/usr/bin/env python3
"""Scan local repositories for deterministic implementation gaps."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

REPO_PAIR_RE = re.compile(r"^([^=]+)=(.+)$")
TODO_FIXME_MARKER_RE = re.compile(
    r"^\s*(?:#|//|/\*+|\*|;|--|<!--|[-*]\s*\[[ xX]\]|[-*])\s*(TODO|FIXME)\b"
)

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
}

TEST_HINTS = (
    "tests/",
    "test_",
    "_test",
    ".spec.",
    ".test.",
)

DOC_FILES = {
    "README.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "SKILL.md",
    ".github/pull_request_template.md",
    "docs/PROJECT_SCOPE.md",
    "docs/SCOPE_TRACKER.md",
}

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

SUGGESTED_SKILLS = {
    "tests_missing": "skill-common-sense-engineering",
    "docs_lockstep_missing": "docs-alignment-lock",
    "todo_fixme_added": "skill-common-sense-engineering",
    "release_hygiene_missing": "skill-arbiter-release-ops",
}

DIFF_MODE_COMMITTED = "committed"
DIFF_MODE_WORKING_TREE = "working-tree"
DIFF_MODE_COMBINED = "combined"
DIFF_MODE_CHOICES = (
    DIFF_MODE_COMMITTED,
    DIFF_MODE_WORKING_TREE,
    DIFF_MODE_COMBINED,
)


@dataclass
class Finding:
    category: str
    severity: str
    summary: str
    evidence: list[str]
    suggested_skill: str


@dataclass
class RepoReport:
    repo: str
    path: str
    merge_base: str
    changed_files: list[str]
    findings: list[Finding]


def run_git(repo_path: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise ValueError(f"git {' '.join(args)} failed in {repo_path}: {message}")
    return result.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-repo deterministic code-gap sweep")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help='Repo mapping as "name=/path/to/repo" (repeatable)',
    )
    parser.add_argument(
        "--repos-root",
        action="append",
        default=[],
        help="Directory containing multiple git repos as immediate child folders (repeatable)",
    )
    parser.add_argument(
        "--exclude-repo",
        action="append",
        default=[],
        help="Repo name to skip after discovery (repeatable)",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=14,
        help="Limit commit walk window for changed-file analysis",
    )
    parser.add_argument(
        "--base-ref",
        default="main",
        help="Preferred base ref for merge-base diff",
    )
    parser.add_argument(
        "--diff-mode",
        choices=DIFF_MODE_CHOICES,
        default=DIFF_MODE_COMBINED,
        help="Diff source mode: committed history, working tree, or both (default: combined)",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional output path for JSON report",
    )
    return parser.parse_args()


def parse_repo_pair(raw: str) -> tuple[str, Path]:
    match = REPO_PAIR_RE.match(str(raw or "").strip())
    if not match:
        raise ValueError(f"invalid --repo value: {raw!r}; expected name=/path/to/repo")
    name = match.group(1).strip()
    path = Path(match.group(2).strip()).expanduser().resolve()
    if not name:
        raise ValueError("repo name cannot be empty")
    if not path.is_dir():
        raise ValueError(f"repo path not found: {path}")
    if not (path / ".git").exists():
        raise ValueError(f"not a git repository: {path}")
    return name, path


def discover_repos_under_root(root: Path) -> list[tuple[str, Path]]:
    if not root.is_dir():
        raise ValueError(f"--repos-root not found: {root}")
    repos: list[tuple[str, Path]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if (child / ".git").exists():
            repos.append((child.name, child.resolve()))
    return repos


def resolve_base_ref(repo_path: Path, base_ref: str) -> str:
    candidates = (f"origin/{base_ref}", base_ref)
    for candidate in candidates:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--verify", "--quiet", candidate],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    return "HEAD~1"


def changed_files(
    repo_path: Path,
    base_ref: str,
    since_days: int,
    diff_mode: str = DIFF_MODE_COMBINED,
) -> tuple[str, list[str]]:
    if diff_mode not in DIFF_MODE_CHOICES:
        raise ValueError(f"invalid diff mode: {diff_mode}")

    resolved_base = resolve_base_ref(repo_path, base_ref)
    merge_base = run_git(repo_path, ["merge-base", "HEAD", resolved_base]).strip()
    if not merge_base:
        merge_base = run_git(repo_path, ["rev-parse", "HEAD~1"]).strip()

    args = ["diff", "--name-only", f"{merge_base}...HEAD"]
    raw = run_git(repo_path, args)
    committed_files = [line.strip() for line in raw.splitlines() if line.strip()]

    if not committed_files and since_days > 0:
        recent_raw = run_git(
            repo_path,
            [
                "log",
                f"--since={since_days} days ago",
                "--name-only",
                "--pretty=format:",
            ],
        )
        committed_files = sorted({line.strip() for line in recent_raw.splitlines() if line.strip()})

    working_raw = run_git(repo_path, ["diff", "--name-only", "HEAD"])
    working_tree_files = [line.strip() for line in working_raw.splitlines() if line.strip()]
    untracked_raw = run_git(repo_path, ["ls-files", "--others", "--exclude-standard"])
    untracked_files = [line.strip() for line in untracked_raw.splitlines() if line.strip()]
    working_tree_files = sorted({*working_tree_files, *untracked_files})

    if diff_mode == DIFF_MODE_COMMITTED:
        files = committed_files
    elif diff_mode == DIFF_MODE_WORKING_TREE:
        files = working_tree_files
    else:
        files = sorted({*committed_files, *working_tree_files})

    return merge_base, files


def is_code_file(path: str) -> bool:
    return Path(path).suffix.lower() in CODE_EXTENSIONS


def is_test_file(path: str) -> bool:
    lower = path.lower()
    return any(hint in lower for hint in TEST_HINTS)


def is_doc_file(path: str) -> bool:
    return path in DOC_FILES or path.startswith("docs/")


def is_release_impacting(path: str) -> bool:
    if path in NON_RELEASE_FILES:
        return False
    if any(path.startswith(prefix) for prefix in NON_RELEASE_PREFIXES):
        return False
    if path.endswith(".md") and path != "SKILL.md":
        return False
    return True


def collect_patch_text(
    repo_path: Path,
    merge_base: str,
    diff_mode: str = DIFF_MODE_COMBINED,
) -> str:
    if diff_mode == DIFF_MODE_COMMITTED:
        return run_git(repo_path, ["diff", "--unified=0", f"{merge_base}...HEAD"])

    if diff_mode == DIFF_MODE_WORKING_TREE:
        return run_git(repo_path, ["diff", "--unified=0", "HEAD"])

    committed_patch = run_git(repo_path, ["diff", "--unified=0", f"{merge_base}...HEAD"])
    working_patch = run_git(repo_path, ["diff", "--unified=0", "HEAD"])
    return committed_patch + "\n" + working_patch


def untracked_todo_fixme_additions(repo_path: Path) -> list[str]:
    raw = run_git(repo_path, ["ls-files", "--others", "--exclude-standard"])
    files = [line.strip() for line in raw.splitlines() if line.strip()]
    evidence: list[str] = []
    for rel in files:
        candidate = repo_path / rel
        if not candidate.is_file():
            continue
        try:
            lines = candidate.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            if TODO_FIXME_MARKER_RE.search(line):
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:117] + "..."
                evidence.append(f"{rel}: +{snippet}")
    return evidence


def todo_fixme_additions(
    repo_path: Path,
    merge_base: str,
    diff_mode: str = DIFF_MODE_COMBINED,
) -> list[str]:
    patch = collect_patch_text(repo_path, merge_base, diff_mode)
    evidence: list[str] = []
    current_file = ""
    for line in patch.splitlines():
        if line.startswith("+++"):
            marker = line[4:].strip()
            current_file = marker[2:] if marker.startswith("b/") else marker
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        if TODO_FIXME_MARKER_RE.search(body):
            snippet = body.strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            evidence.append(f"{current_file}: +{snippet}")

    if diff_mode in (DIFF_MODE_WORKING_TREE, DIFF_MODE_COMBINED):
        evidence.extend(untracked_todo_fixme_additions(repo_path))

    # Keep deterministic ordering and remove duplicates.
    deduped = sorted(set(evidence))
    return deduped


def analyze_repo(
    name: str,
    repo_path: Path,
    base_ref: str,
    since_days: int,
    diff_mode: str = DIFF_MODE_COMBINED,
) -> RepoReport:
    merge_base, files = changed_files(repo_path, base_ref, since_days, diff_mode)
    findings: list[Finding] = []

    code_changed = sorted(path for path in files if is_code_file(path) and not is_test_file(path))
    tests_changed = sorted(path for path in files if is_test_file(path))
    docs_changed = sorted(path for path in files if is_doc_file(path))

    if code_changed and not tests_changed:
        findings.append(
            Finding(
                category="tests_missing",
                severity="high",
                summary="Code files changed without corresponding test file changes.",
                evidence=code_changed[:20],
                suggested_skill=SUGGESTED_SKILLS["tests_missing"],
            )
        )

    behavior_changes = [path for path in files if is_release_impacting(path)]
    if behavior_changes and not docs_changed:
        findings.append(
            Finding(
                category="docs_lockstep_missing",
                severity="medium",
                summary="Behavior-impacting files changed without doc lockstep updates.",
                evidence=behavior_changes[:20],
                suggested_skill=SUGGESTED_SKILLS["docs_lockstep_missing"],
            )
        )

    todo_added = todo_fixme_additions(repo_path, merge_base, diff_mode)
    if todo_added:
        findings.append(
            Finding(
                category="todo_fixme_added",
                severity="medium",
                summary="Added TODO/FIXME markers detected in patch.",
                evidence=todo_added[:20],
                suggested_skill=SUGGESTED_SKILLS["todo_fixme_added"],
            )
        )

    has_release_contract = (repo_path / "pyproject.toml").is_file() and (repo_path / "CHANGELOG.md").is_file()
    if behavior_changes and has_release_contract:
        changed_set = set(files)
        has_release_files = "pyproject.toml" in changed_set and "CHANGELOG.md" in changed_set
        if not has_release_files:
            findings.append(
                Finding(
                    category="release_hygiene_missing",
                    severity="critical",
                    summary="Release-impacting files changed without pyproject/changelog update.",
                    evidence=behavior_changes[:20],
                    suggested_skill=SUGGESTED_SKILLS["release_hygiene_missing"],
                )
            )

    return RepoReport(
        repo=name,
        path=str(repo_path),
        merge_base=merge_base,
        changed_files=files,
        findings=findings,
    )


def aggregate(reports: list[RepoReport]) -> dict[str, Any]:
    categories: dict[str, int] = {}
    severities: dict[str, int] = {}
    suggested: dict[str, int] = {}

    for report in reports:
        for finding in report.findings:
            categories[finding.category] = categories.get(finding.category, 0) + 1
            severities[finding.severity] = severities.get(finding.severity, 0) + 1
            suggested[finding.suggested_skill] = suggested.get(finding.suggested_skill, 0) + 1

    return {
        "categories": dict(sorted(categories.items())),
        "severities": dict(sorted(severities.items())),
        "suggested_skills": dict(sorted(suggested.items())),
    }


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def to_jsonable_report(report: RepoReport) -> dict[str, Any]:
    data = asdict(report)
    data["findings"] = [asdict(item) for item in report.findings]
    return data


def main() -> int:
    args = parse_args()

    repos: list[tuple[str, Path]] = []
    seen_names: set[str] = set()
    for raw in args.repo:
        try:
            name, path = parse_repo_pair(raw)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if name in seen_names:
            print(f"error: duplicate repo name: {name}", file=sys.stderr)
            return 2
        seen_names.add(name)
        repos.append((name, path))

    for raw_root in args.repos_root:
        root = Path(str(raw_root).strip()).expanduser().resolve()
        try:
            discovered = discover_repos_under_root(root)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for name, path in discovered:
            if name in seen_names:
                continue
            seen_names.add(name)
            repos.append((name, path))

    excludes = {str(item or "").strip() for item in args.exclude_repo if str(item or "").strip()}
    if excludes:
        repos = [(name, path) for name, path in repos if name not in excludes]

    if not repos:
        print(
            "error: no repositories selected; provide --repo name=/path and/or --repos-root /path",
            file=sys.stderr,
        )
        return 2

    reports: list[RepoReport] = []
    errors: list[str] = []
    for name, path in repos:
        try:
            reports.append(analyze_repo(name, path, args.base_ref, args.since_days, args.diff_mode))
        except ValueError as exc:
            errors.append(str(exc))

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_ref": args.base_ref,
        "since_days": args.since_days,
        "diff_mode": args.diff_mode,
        "repos": [to_jsonable_report(report) for report in reports],
        "aggregate": aggregate(reports),
        "errors": errors,
    }

    write_json(args.json_out, payload)

    print("repo,findings,critical,high,medium")
    for report in reports:
        crit = sum(1 for item in report.findings if item.severity == "critical")
        high = sum(1 for item in report.findings if item.severity == "high")
        med = sum(1 for item in report.findings if item.severity == "medium")
        print(f"{report.repo},{len(report.findings)},{crit},{high},{med}")

    if errors:
        for item in errors:
            print(f"error: {item}", file=sys.stderr)
        return 1

    critical_count = payload["aggregate"]["severities"].get("critical", 0)
    if critical_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
