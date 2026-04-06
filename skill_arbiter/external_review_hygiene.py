from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .privacy_policy import tracked_paths


MARKER_PATTERNS = (
    ("vendor_name", re.compile(r"(?i)\b(?:tessl|tesslio)\b")),
    ("vendor_secret", re.compile(r"\bTESSL_API_TOKEN\b")),
    ("vendor_workflow", re.compile(r"(?i)\bskill-review(?:-and-optimize)?\b")),
    ("vendor_apply_command", re.compile(r"(?i)\b/?apply-optimize\b")),
)

WORKFLOW_USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<target>\S+)")
GOVERNED_PREFIXES = (
    ".github/",
    "scripts/",
    "skill_arbiter/",
    "apps/",
    "skill-candidates/",
)


@dataclass
class ExternalReviewFinding:
    path: str
    line: int
    col: int
    kind: str
    snippet: str


@dataclass
class ExternalReviewScanResult:
    passed: bool
    findings: list[ExternalReviewFinding]
    scope: str


def _run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def _changed_paths(repo_root: Path, base_ref: str) -> list[Path]:
    output = _run_git(repo_root, ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...HEAD"])
    paths: list[Path] = []
    for raw in output.splitlines():
        path_text = raw.strip()
        if not path_text:
            continue
        path = repo_root / path_text
        if path.is_file():
            paths.append(path)
    return paths


def _is_governed_surface(repo_root: Path, path: Path) -> bool:
    rel = path.relative_to(repo_root).as_posix()
    return rel.startswith(GOVERNED_PREFIXES)


def scan_paths(repo_root: Path, paths: list[Path], *, scope: str = "custom-paths") -> ExternalReviewScanResult:
    findings: list[ExternalReviewFinding] = []
    for path in paths:
        if not _is_governed_surface(repo_root, path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        is_workflow = rel_path.startswith(".github/workflows/") and rel_path.endswith((".yml", ".yaml"))
        for line_num, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in MARKER_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                findings.append(
                    ExternalReviewFinding(
                        path=rel_path,
                        line=line_num,
                        col=match.start() + 1,
                        kind=kind,
                        snippet=match.group(0),
                    )
                )
            if is_workflow:
                match = WORKFLOW_USES_RE.search(line)
                if match:
                    target = match.group("target")
                    if not target.startswith("./"):
                        findings.append(
                            ExternalReviewFinding(
                                path=rel_path,
                                line=line_num,
                                col=match.start("target") + 1,
                                kind="non_local_workflow_uses",
                                snippet=target,
                            )
                        )
    return ExternalReviewScanResult(passed=not findings, findings=findings, scope=scope)


def scan_repo(repo_root: Path, staged: bool = False, base_ref: str = "") -> ExternalReviewScanResult:
    if staged:
        paths = tracked_paths(repo_root, staged=True)
        return scan_paths(repo_root, paths, scope="staged-files")
    if base_ref.strip():
        paths = _changed_paths(repo_root, base_ref.strip())
        return scan_paths(repo_root, paths, scope="diff-files")
    paths = tracked_paths(repo_root, staged=False)
    return scan_paths(repo_root, paths, scope="tracked-files")
