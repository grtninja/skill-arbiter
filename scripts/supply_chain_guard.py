#!/usr/bin/env python3
"""Deterministic supply-chain risk detection for skill admission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.paths import windows_no_window_subprocess_kwargs

MAX_READ_BYTES = 512 * 1024
TEXT_SCAN_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".py",
    ".ps1",
    ".bat",
    ".cmd",
    ".sh",
    ".bash",
    ".zsh",
}
LIVE_TEXT_DIRS = {
    "agents",
    "scripts",
    "assets",
    "templates",
    "config",
}

PACKAGE_MANAGER_INSTALL_RE = re.compile(
    r"(?P<tool>npm|pnpm|yarn|bun|pip(?:3)?)"
    r"(?:\s+(?P<subcmd>install|add|i|dlx|exec|global|global\s+add))"
    r"(?P<args>[^\n\r]*)",
    flags=re.IGNORECASE,
)
NPX_LIKE_RE = re.compile(r"\b(?P<tool>npx|pnpm\s+dlx|bunx)\s+(?P<args>[^\n\r]+)", flags=re.IGNORECASE)

REMOTE_EXECUTION_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "curl_pipe_shell", r"curl\s+[^|\n\r]+?\|\s*(?:sh|bash|zsh|pwsh|powershell)\b"),
    ("critical", "wget_pipe_shell", r"wget\s+[^|\n\r]+?\|\s*(?:sh|bash|zsh|pwsh|powershell)\b"),
    ("high", "invoke_expression", r"\binvoke-expression\b"),
    ("high", "powershell_iex", r"(?<![A-Za-z0-9_])iex(?![A-Za-z0-9_])"),
    ("high", "encoded_command", r"-enc(?:odedcommand)?\s+[A-Za-z0-9+/=]{16,}"),
    ("high", "frombase64", r"frombase64string\s*\("),
)
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

RUNAWAY_PROCESS_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "detached_pythonw", r"\bpythonw(?:\.exe)?\b"),
    ("high", "hidden_process_launch", r"start-process[^\n\r]+-windowstyle\s+hidden"),
    ("high", "detached_subprocess", r"creationflags\s*=\s*subprocess\.(?:detached_process|create_new_process_group)|start_new_session\s*=\s*true"),
    ("high", "background_job_spawn", r"\bstart-job\b|\bnohup\b|\bdaemon\s*=\s*true"),
    ("high", "broad_process_kill", r"get-nettcpconnection[^\n\r]+stop-process|taskkill(?:\.exe)?\s+/f|\bstop-process\b[^\n\r]+-force|\bpkill\b|\bkillall\b"),
    ("medium", "browser_autolaunch", r"window\.open\(|start-process\s+https?://|explorer(?:\.exe)?\s+https?://"),
)
CROSS_AGENT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("medium", "openclaw_nullclaw_tool_surface", r"\bopenclaw\b|\bnullclaw\b"),
    ("medium", "agent_tools_definition", r"(^|\n)\s*tools\s*:\s|\b/api/agent\b|\bmcp\b"),
    ("medium", "agent_resources_definition", r"(^|\n)\s*resources\s*:\s|\b/api/resources\b"),
)
PERSISTENCE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "npm_global_bin_persistence", r"appdata\\roaming\\npm|/usr/local/bin|~/\.local/bin"),
    ("high", "scheduled_task", r"\bschtasks(?:\.exe)?\b|\bnew-scheduledtask\b"),
    ("high", "registry_run_key", r"currentversion\\run|reg\s+add\s+hk[lc]m\\software\\microsoft\\windows\\currentversion\\run"),
    ("high", "launch_agents", r"launchagents|launchdaemons"),
    ("high", "shell_profile_persistence", r"\.(?:bashrc|zshrc|profile|bash_profile|zprofile)\b"),
    ("high", "crontab_persistence", r"\bcrontab\b"),
)
CREDENTIAL_THEFT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "fake_password_prompt", r"password prompt|enter your (?:system )?password|sudo password"),
    ("critical", "silent_password_read", r"\bread\s+-s\b"),
    ("critical", "osascript_password_dialog", r"osascript[^\n\r]+display dialog[^\n\r]+password"),
    ("high", "get_credential", r"\bget-credential\b|\bpromptforcredential\b"),
    ("high", "read_host_secure", r"read-host\s+-assecurestring"),
)
PYTHON_BINARY_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("critical", "python_launcher_spoof", r"copy-item[^\n\r]+python(?:w)?\.exe|rename-item[^\n\r]+python(?:w)?\.exe"),
    ("critical", "python_binary_copy", r"shutil\.(?:copy|copy2|copyfile)\([^\n\r]+python(?:w)?\.exe"),
)
BLOCKED_PACKAGES = {
    "@openclaw-ai/openclawai",
    "openclawai",
}
TRUSTED_BRANDS = {
    "openclaw",
    "openai",
    "codex",
    "claude",
    "anthropic",
    "memryx",
    "starframe",
}
STALE_PYTHON_NAME_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("high", "hidden_python_script", r"(^|[\\/])\.[^\\/]+\.py$"),
    ("high", "backup_python_script", r"(^|[\\/]).*(?:backup|bak|old|copy|tmp|temp|stale)[^\\/]*\.py$"),
    ("high", "editor_swap_python_script", r"(^|[\\/]).*\.py(?:\.swp|\.tmp|~)$"),
)
APPROVED_PYTHON_DIRS = {"scripts", "tests", "assets", "examples"}


def _is_live_text_surface(skill_dir: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(skill_dir)
    except ValueError:
        return False
    if not rel.parts:
        return False
    first = rel.parts[0].lower()
    if first == "references":
        return False
    if rel.name.lower() == "skill.md":
        return True
    if first in LIVE_TEXT_DIRS:
        return True
    if len(rel.parts) == 1 and path.suffix.lower() in {
        ".py",
        ".ps1",
        ".bat",
        ".cmd",
        ".sh",
        ".bash",
        ".zsh",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
    }:
        return True
    return False


@dataclass(frozen=True)
class SupplyChainFinding:
    severity: str
    code: str
    message: str


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    for i, left_ch in enumerate(left, start=1):
        curr = [i]
        for j, right_ch in enumerate(right, start=1):
            cost = 0 if left_ch == right_ch else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _extract_packages(args: str) -> list[str]:
    packages: list[str] = []
    for token in re.split(r"\s+", args.strip()):
        item = token.strip().strip("\"'`,")
        if not item or item.startswith("-"):
            continue
        if item in {"&&", ";", "|"}:
            break
        packages.append(item)
    return packages


def _find_install_commands(content: str) -> list[tuple[str, str, list[str]]]:
    rows: list[tuple[str, str, list[str]]] = []
    for match in PACKAGE_MANAGER_INSTALL_RE.finditer(content):
        tool = str(match.group("tool") or "").lower()
        args = str(match.group("args") or "")
        rows.append((tool, args, _extract_packages(args)))
    for match in NPX_LIKE_RE.finditer(content):
        tool = str(match.group("tool") or "").lower()
        args = str(match.group("args") or "")
        rows.append((tool, args, _extract_packages(args)))
    return rows


def _detect_typosquat(package: str) -> str | None:
    normalized = _normalize_name(package.split("@", 1)[-1] if package.startswith("@") else package)
    if not normalized:
        return None
    for brand in TRUSTED_BRANDS:
        candidate = _normalize_name(brand)
        if normalized == candidate:
            continue
        if candidate and _levenshtein(normalized, candidate) == 1:
            return brand
    return None


def scan_content(content: str) -> list[SupplyChainFinding]:
    lowered = content.lower()
    findings: list[SupplyChainFinding] = []
    seen: set[tuple[str, str, str]] = set()

    def add(severity: str, code: str, message: str) -> None:
        key = (severity, code, message)
        if key in seen:
            return
        seen.add(key)
        findings.append(SupplyChainFinding(severity=severity, code=code, message=message))

    for severity, code, pattern in REMOTE_EXECUTION_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            add(severity, code, f"matched remote-execution pattern '{code}'")
    for severity, code, pattern in RUNAWAY_PROCESS_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            add(severity, code, f"matched runaway-process pattern '{code}'")
    cross_agent_hit = False
    for severity, code, pattern in CROSS_AGENT_PATTERNS:
        matched = re.search(pattern, content, flags=re.IGNORECASE | re.MULTILINE)
        if matched:
            add(severity, code, f"matched cross-agent/tooling pattern '{code}'")
            cross_agent_hit = True
    for severity, code, pattern in PERSISTENCE_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            add(severity, code, f"matched persistence pattern '{code}'")
    for severity, code, pattern in CREDENTIAL_THEFT_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            add(severity, code, f"matched credential-access pattern '{code}'")
    for severity, code, pattern in PYTHON_BINARY_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            add(severity, code, f"matched python-binary pattern '{code}'")

    for tool, args, packages in _find_install_commands(content):
        raw = f"{tool} {args}".strip()
        if re.search(r"(?:^|\s)(?:-g|--global)(?:\s|$)", raw):
            add("critical", "global_install_command", f"global package install detected: {raw[:160]}")
        if tool in {"npx", "pnpm dlx", "bunx"}:
            add("high", "ephemeral_exec_command", f"ephemeral package execution detected: {raw[:160]}")
        for package in packages:
            lowered_pkg = package.lower()
            if lowered_pkg in BLOCKED_PACKAGES:
                add("critical", "known_blocked_package", f"known blocked package referenced: {package}")
            typosquat_brand = _detect_typosquat(package)
            if typosquat_brand:
                add("high", "possible_typosquat_package", f"package '{package}' is one edit away from trusted brand '{typosquat_brand}'")
    if cross_agent_hit and any(item.code in {"global_install_command", "ephemeral_exec_command"} for item in findings):
        add("critical", "cross_agent_remote_install", "cross-agent tool/resource surface paired with remote package execution")

    findings.sort(key=lambda item: (SEVERITY_ORDER.get(item.severity, 9), item.code, item.message))
    return findings


def summarize_findings(findings: Iterable[SupplyChainFinding]) -> dict[str, object]:
    rows = list(findings)
    blocker_count = sum(1 for item in rows if item.severity == "critical")
    warning_count = sum(1 for item in rows if item.severity == "high")
    return {
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "codes": [item.code for item in rows],
        "findings": [asdict(item) for item in rows],
    }


def _find_git_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


@lru_cache(maxsize=8)
def _git_untracked_python_rows(git_root_text: str) -> tuple[str, ...]:
    git_root = Path(git_root_text)
    result = subprocess.run(
        ["git", "-C", str(git_root), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True,
        text=True,
        check=False,
        **windows_no_window_subprocess_kwargs(),
    )
    if result.returncode != 0:
        return ()
    rows: list[str] = []
    for line in result.stdout.splitlines():
        if not line.startswith("?? "):
            continue
        path_text = line[3:].strip().replace("\\", "/")
        if path_text.lower().endswith(".py"):
            rows.append(path_text)
    return tuple(sorted(set(rows)))


def _git_untracked_python(skill_dir: Path, source_root: Path) -> list[str]:
    git_root = _find_git_root(source_root)
    if git_root is None:
        return []
    try:
        target = skill_dir.resolve().relative_to(git_root.resolve())
    except ValueError:
        return []
    prefix = str(target).replace("\\", "/").rstrip("/")
    rows = [
        path_text
        for path_text in _git_untracked_python_rows(str(git_root.resolve()))
        if path_text == prefix or path_text.startswith(prefix + "/")
    ]
    return sorted(set(rows))


def scan_skill_tree(skill_dir: Path, source_root: Path) -> list[SupplyChainFinding]:
    findings: list[SupplyChainFinding] = []
    seen: set[tuple[str, str, str]] = set()

    def add(severity: str, code: str, message: str) -> None:
        key = (severity, code, message)
        if key in seen:
            return
        seen.add(key)
        findings.append(SupplyChainFinding(severity=severity, code=code, message=message))

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(skill_dir)).replace("\\", "/")
        filename = path.name.lower()
        if filename in {"python.exe", "pythonw.exe"} or (
            path.suffix.lower() == ".exe" and filename.startswith(("python-", "pythonw-"))
        ):
            add("critical", "vendored_python_binary", f"vendored python binary detected: {rel}")
        if rel.lower().endswith(".py"):
            top_level = rel.split("/", 1)[0].lower()
            if top_level not in APPROVED_PYTHON_DIRS:
                add("high", "python_outside_expected_dirs", f"python file outside expected dirs: {rel}")
        for severity, code, pattern in STALE_PYTHON_NAME_PATTERNS:
            if re.search(pattern, rel, flags=re.IGNORECASE):
                add(severity, code, f"stale or hidden python artifact detected: {rel}")

    for rel in _git_untracked_python(skill_dir, source_root):
        add("critical", "untracked_python_script", f"untracked python script detected by git: {rel}")

    findings.sort(key=lambda item: (SEVERITY_ORDER.get(item.severity, 9), item.code, item.message))
    return findings


def scan_skill_dir_content(skill_dir: Path) -> list[SupplyChainFinding]:
    parts: list[str] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SCAN_SUFFIXES:
            continue
        if not _is_live_text_surface(skill_dir, path):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_READ_BYTES:
            continue
        parts.append(data.decode("utf-8", errors="replace"))
    return scan_content("\n".join(parts))
