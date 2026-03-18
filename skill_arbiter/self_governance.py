from __future__ import annotations

import json
import re
from pathlib import Path

from .contracts import SelfGovernanceFinding
from .paths import REPO_ROOT
from .privacy_policy import scan_repo

SELF_GOVERNANCE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "browser_autolaunch", r"\bwebbrowser\.open\b|Start-Process\s+https?://|explorer(?:\.exe)?\s+https?://"),
    ("critical", "scheduled_task", r"\bschtasks(?:\.exe)?\b|\bNew-ScheduledTask\b"),
    ("high", "hidden_process_launch", r"Start-Process[^\n\r]+-WindowStyle\s+Hidden|CREATE_NO_WINDOW"),
    ("high", "vendored_python_binary", r"copy-item[^\n\r]+python(?:w)?\.exe|rename-item[^\n\r]+python(?:w)?\.exe"),
    ("high", "path_pollution", r"\bsetx\s+PATH\b|\$env:PATH\s*=|export\s+PATH="),
)
SCAN_SUFFIXES = {".py", ".ps1", ".md", ".yaml", ".yml", ".json", ".toml"}
SCAN_ROOTS = ("scripts", "skill_arbiter", "README.md", "BOUNDARIES.md", "SECURITY.md", "SKILL.md")


def _iter_scan_files(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for name in SCAN_ROOTS:
        path = repo_root / name
        if path.is_file():
            paths.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in SCAN_SUFFIXES:
                    paths.append(child)
    return paths


def run_self_governance_scan(repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or REPO_ROOT
    privacy = scan_repo(root)
    findings: list[SelfGovernanceFinding] = [
        SelfGovernanceFinding(
            severity="critical",
            code="privacy_leak",
            message=f"{item.kind}: {item.snippet}",
            path=item.path,
        )
        for item in privacy.findings
    ]
    seen: set[tuple[str, str, str, str]] = set()
    for path in _iter_scan_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for severity, code, pattern in SELF_GOVERNANCE_PATTERNS:
            if rel == "scripts/nullclaw_desktop.py" and code == "hidden_process_launch":
                continue
            if rel == "scripts/start_security_console.ps1" and code == "hidden_process_launch":
                continue
            if rel == "skill_arbiter/self_governance.py":
                continue
            if re.search(pattern, text, flags=re.IGNORECASE):
                row = (severity, code, rel, pattern)
                if row in seen:
                    continue
                seen.add(row)
                findings.append(
                    SelfGovernanceFinding(
                        severity=severity,
                        code=code,
                        message=f"matched self-governance pattern '{code}'",
                        path=rel,
                    )
                )
    return {
        "passed": not findings,
        "privacy_passed": privacy.passed,
        "critical_count": sum(1 for item in findings if item.severity == "critical"),
        "high_count": sum(1 for item in findings if item.severity == "high"),
        "findings": [item.to_dict() for item in findings],
    }


def write_self_governance_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
