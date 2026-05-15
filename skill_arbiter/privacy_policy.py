from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .contracts import PrivacyFinding
from .paths import windows_no_window_subprocess_kwargs

EXPORT_EXCLUDE_FILE = Path("public/export-exclude.txt")
PRIVATE_SURFACE_PREFIXES = ("skill_arbiter/private/", "tests/private/")
REDACTED_SNIPPET = "[redacted for privacy]"

SEALED_PRIVATE_TEXT_PATTERNS = (
    re.compile(r"\bTOP_SECRET_LOCAL_ONLY\s*=\s*True\b"),
    re.compile(r"\bPRIVATE_EXTENSION_KIND\s*="),
    re.compile(r"\bskill_arbiter\.private\b"),
    re.compile(r"\bnaughty_mode\b", re.IGNORECASE),
    re.compile(r"\bMaidPersonaContract\b"),
    re.compile(r"\bNaughtyModeContract\b"),
)

USER_PATH_PATTERNS = (
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"/Users/[A-Za-z0-9._ -]+/"),
    re.compile(r"/mnt/[A-Za-z]/Users/[A-Za-z0-9._ -]+/"),
    re.compile(r"[A-Za-z]:/Users/[A-Za-z0-9._ -]+/"),
    re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._ -]+\\"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._ -]+\\\\"),
)

SENSITIVE_TOKEN_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9][A-Za-z0-9-]*-Internal\b"),
    re.compile(r"\b[A-Za-z0-9]+---[A-Za-z0-9]+\b"),
    re.compile(r"\b[a-z0-9-]+-python-shim\b", re.IGNORECASE),
    re.compile(r"\b[A-Z][A-Za-z0-9-]*-Sandbox\b"),
    re.compile(r"GitHub[\\\\/](?!<)[A-Za-z0-9._-]+"),
    re.compile(r"\bSTARFRAME_SINGLE_SOURCE_OF_TRUTH(?:\.md)?\b", re.IGNORECASE),
    re.compile(r"\bSTARFRAME\s*SSOT\b", re.IGNORECASE),
    re.compile(r"\bSINGLE[_-]SOURCE[_-]OF[_-]TRUTH\b", re.IGNORECASE),
)

ROOT_HINT_RE = re.compile(r"Run from `([^`]+)` root:")
REPO_TOKEN_RE = re.compile(r"[A-Za-z0-9]+-[A-Za-z0-9-]+")


@dataclass
class PrivacyScanResult:
    passed: bool
    findings: list[PrivacyFinding]
    scope: str


def _redacted_finding(path: str, line: int, col: int, kind: str) -> PrivacyFinding:
    return PrivacyFinding(path=path, line=line, col=col, kind=kind, snippet=REDACTED_SNIPPET)


def _is_private_surface(rel_path: str) -> bool:
    return rel_path.startswith(PRIVATE_SURFACE_PREFIXES)


def _run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        **windows_no_window_subprocess_kwargs(),
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def tracked_paths(repo_root: Path, staged: bool = False) -> list[Path]:
    output = _run_git(
        repo_root,
        ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"] if staged else ["ls-files"],
    )
    paths: list[Path] = []
    for raw in output.splitlines():
        path_text = raw.strip()
        if not path_text:
            continue
        path = repo_root / path_text
        if path.is_file():
            paths.append(path)
    return paths


def is_binary(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\x00" in sample


def scan_text(repo_root: Path, path: Path, text: str) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    rel_path = path.relative_to(repo_root).as_posix()
    if _is_private_surface(rel_path):
        findings.append(_redacted_finding(rel_path, 1, 1, "local-only-private-surface"))
    for line_num, line in enumerate(text.splitlines(), start=1):
        for pattern in SEALED_PRIVATE_TEXT_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    _redacted_finding(rel_path, line_num, match.start() + 1, "local-only-private-surface")
                )
        for pattern in USER_PATH_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(_redacted_finding(rel_path, line_num, match.start() + 1, "user-absolute-path"))
        for pattern in SENSITIVE_TOKEN_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    _redacted_finding(rel_path, line_num, match.start() + 1, "private-repo-identifier")
                )
        if rel_path.startswith("skill-candidates/") and path.name in {"SKILL.md", "openai.yaml"}:
            root_match = ROOT_HINT_RE.search(line)
            if root_match:
                target = root_match.group(1).strip()
                if not (target.startswith("<") or target.startswith("/path/") or target.startswith("$")):
                    findings.append(
                        _redacted_finding(
                            rel_path, line_num, root_match.start(1) + 1, "repo-placeholder-required"
                        )
                    )
            if line.startswith("description:") and " in " in line and "<" not in line:
                suffix = line.split(" in ", 1)[1]
                token_match = REPO_TOKEN_RE.search(suffix)
                if token_match:
                    token = token_match.group(0)
                    if token != "skill-arbiter":
                        findings.append(
                            _redacted_finding(
                                rel_path,
                                line_num,
                                token_match.start() + line.find(suffix) + 1,
                                "repo-placeholder-required",
                            )
                        )
    return findings


def scan_paths(repo_root: Path, paths: list[Path]) -> PrivacyScanResult:
    findings: list[PrivacyFinding] = []
    for path in paths:
        if is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        findings.extend(scan_text(repo_root, path, text))
    return PrivacyScanResult(passed=not findings, findings=findings, scope="custom-paths")


def scan_repo(repo_root: Path, staged: bool = False) -> PrivacyScanResult:
    paths = tracked_paths(repo_root, staged=staged)
    result = scan_paths(repo_root, paths)
    result.scope = "staged-files" if staged else "tracked-files"
    return result
