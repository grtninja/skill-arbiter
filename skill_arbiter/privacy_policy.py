from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .contracts import PrivacyFinding
from .paths import windows_no_window_subprocess_kwargs

EXPORT_EXCLUDE_FILE = Path("public/export-exclude.txt")
PRIVATE_SURFACE_PREFIXES = ("skill_arbiter/private/", "tests/private/")
SEALED_PRIVATE_TEXT_PATTERNS = (
    re.compile(r"\bTOP_SECRET_LOCAL_ONLY\s*=\s*True\b"),
    re.compile(r"\bPRIVATE_EXTENSION_KIND\s*="),
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


def _redacted_snippet(kind: str, raw: str) -> str:
    if kind in {"user-absolute-path", "private-repo-identifier", "repo-placeholder-required"}:
        return "[redacted for privacy]"
    if not raw:
        return "[redacted]"
    if len(raw) > 128:
        return "[redacted]"
    return raw


def _is_private_surface_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in PRIVATE_SURFACE_PREFIXES)


def _contains_private_surface_hint(text: str) -> bool:
    return any(pattern.search(text) for pattern in SEALED_PRIVATE_TEXT_PATTERNS)


def load_export_exclude_rules(repo_root: Path) -> tuple[str, ...]:
    path = repo_root / EXPORT_EXCLUDE_FILE
    if not path.is_file():
        return ()
    rules: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        rule = raw.strip().replace("\\", "/")
        if not rule or rule.startswith("#"):
            continue
        rules.append(rule)
    return tuple(rules)


def path_excluded_from_public_export(repo_root: Path, relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    for rule in load_export_exclude_rules(repo_root):
        if rule.endswith("/"):
            if normalized.startswith(rule):
                return True
            continue
        if normalized == rule:
            return True
    return False


def _private_surface_findings(relative_path: str, text: str) -> list[PrivacyFinding]:
    normalized = relative_path.replace("\\", "/")
    if not _is_private_surface_path(normalized):
        if normalized.startswith("tests/"):
            return []
        if not _contains_private_surface_hint(text):
            return []
    return [
        PrivacyFinding(
            path=relative_path,
            line=1,
            col=1,
            kind="local-only-private-surface",
            snippet="Local-only private surface: must not be included in public-shape artifacts.",
        )
    ]


@dataclass
class PrivacyScanResult:
    passed: bool
    findings: list[PrivacyFinding]
    scope: str


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


def tracked_paths(repo_root: Path, staged: bool = False, *, respect_export_excludes: bool = True) -> list[Path]:
    output = _run_git(
        repo_root,
        ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"] if staged else ["ls-files"],
    )
    paths: list[Path] = []
    for raw in output.splitlines():
        path_text = raw.strip()
        if not path_text:
            continue
        if respect_export_excludes and path_excluded_from_public_export(repo_root, path_text):
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
    for line_num, line in enumerate(text.splitlines(), start=1):
        for pattern in USER_PATH_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    PrivacyFinding(
                        path=rel_path,
                        line=line_num,
                        col=match.start() + 1,
                        kind="user-absolute-path",
                        snippet=_redacted_snippet("user-absolute-path", match.group(0)),
                    )
                )
        for pattern in SENSITIVE_TOKEN_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append(
                    PrivacyFinding(
                        path=rel_path,
                        line=line_num,
                        col=match.start() + 1,
                        kind="private-repo-identifier",
                        snippet=_redacted_snippet("private-repo-identifier", match.group(0)),
                    )
                )
        if rel_path.startswith("skill-candidates/") and path.name in {"SKILL.md", "openai.yaml"}:
            root_match = ROOT_HINT_RE.search(line)
            if root_match:
                target = root_match.group(1).strip()
                if not (target.startswith("<") or target.startswith("/path/") or target.startswith("$")):
                    findings.append(
                        PrivacyFinding(
                            path=rel_path,
                            line=line_num,
                            col=root_match.start(1) + 1,
                            kind="repo-placeholder-required",
                            snippet=_redacted_snippet(
                                "repo-placeholder-required",
                                target,
                            ),
                        )
                    )
            if line.startswith("description:") and " in " in line and "<" not in line:
                suffix = line.split(" in ", 1)[1]
                token_match = REPO_TOKEN_RE.search(suffix)
                if token_match:
                    token = token_match.group(0)
                    if token != "skill-arbiter":
                        findings.append(
                            PrivacyFinding(
                                path=rel_path,
                                line=line_num,
                                col=token_match.start() + line.find(suffix) + 1,
                                kind="repo-placeholder-required",
                                snippet=_redacted_snippet("repo-placeholder-required", token),
                            )
                        )
    return findings


def scan_paths(repo_root: Path, paths: list[Path]) -> PrivacyScanResult:
    findings: list[PrivacyFinding] = []
    for path in paths:
        if is_binary(path):
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        findings.extend(_private_surface_findings(rel_path, text))
        findings.extend(scan_text(repo_root, path, text))
    return PrivacyScanResult(passed=not findings, findings=findings, scope="custom-paths")


def scan_repo(repo_root: Path, staged: bool = False, *, respect_export_excludes: bool = True) -> PrivacyScanResult:
    paths = tracked_paths(repo_root, staged=staged, respect_export_excludes=respect_export_excludes)
    result = scan_paths(repo_root, paths)
    result.scope = "staged-files" if staged else "tracked-files"
    return result
