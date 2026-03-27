from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .privacy_policy import is_binary, tracked_paths


SECRET_PATTERNS = (
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{24,}")),
    ("generic_api_key_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
)

ALLOWED_SNIPPETS = (
    "<token>",
    "<api-key>",
    "<api_key>",
    "<secret>",
    "example",
    "placeholder",
    "redacted",
    "masked",
    "test",
    "fake",
    "dummy",
    "_here",
    "your-token-here",
    "replace-me",
    "resume-token",
    "${{ secrets.",
)


@dataclass
class SecretFinding:
    path: str
    line: int
    col: int
    kind: str
    snippet: str


@dataclass
class SecretScanResult:
    passed: bool
    findings: list[SecretFinding]
    scope: str


def _should_ignore(line: str, snippet: str) -> bool:
    lowered = f"{line} {snippet}".lower()
    return any(token in lowered for token in ALLOWED_SNIPPETS)


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


def scan_paths(repo_root: Path, paths: list[Path], *, scope: str = "custom-paths") -> SecretScanResult:
    findings: list[SecretFinding] = []
    for path in paths:
        if is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        for line_num, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                snippet = match.group(0)
                if _should_ignore(line, snippet):
                    continue
                findings.append(
                    SecretFinding(
                        path=rel_path,
                        line=line_num,
                        col=match.start() + 1,
                        kind=kind,
                        snippet=snippet,
                    )
                )
    return SecretScanResult(passed=not findings, findings=findings, scope=scope)


def scan_repo(repo_root: Path, staged: bool = False, base_ref: str = "") -> SecretScanResult:
    if staged:
        paths = tracked_paths(repo_root, staged=True)
        result = scan_paths(repo_root, paths, scope="staged-files")
        return result
    if base_ref.strip():
        paths = _changed_paths(repo_root, base_ref.strip())
        return scan_paths(repo_root, paths, scope="diff-files")
    paths = tracked_paths(repo_root, staged=False)
    result = scan_paths(repo_root, paths, scope="tracked-files")
    return result
