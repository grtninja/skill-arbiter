from __future__ import annotations

import hashlib
import os
import socket
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_ROOT = Path.home() / ".codex" / "skills"
DEFAULT_CANDIDATES_ROOT = REPO_ROOT / "skill-candidates"
DEFAULT_AGENT_HOST = "127.0.0.1"
DEFAULT_AGENT_PORT = 17665


def windows_no_window_subprocess_kwargs(kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized: dict[str, Any] = dict(kwargs or {})
    if os.name != "nt":
        return normalized

    startupinfo_obj = normalized.get("startupinfo")
    startupinfo_type = getattr(subprocess, "STARTUPINFO", None)
    if startupinfo_type is not None and startupinfo_obj is None:
        startupinfo_obj = startupinfo_type()
    if startupinfo_obj is not None:
        startf_use_show_window = int(getattr(subprocess, "STARTF_USESHOWWINDOW", 0))
        if hasattr(startupinfo_obj, "dwFlags"):
            startupinfo_obj.dwFlags |= startf_use_show_window
        if hasattr(startupinfo_obj, "wShowWindow"):
            startupinfo_obj.wShowWindow = 0
        normalized["startupinfo"] = startupinfo_obj
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if creationflags:
        normalized["creationflags"] = int(normalized.get("creationflags") or 0) | creationflags
    return normalized


def state_root() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "SkillArbiterNullClaw"
    return Path.home() / "AppData" / "Local" / "SkillArbiterNullClaw"


def ensure_state_dirs() -> Path:
    root = state_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "cache").mkdir(parents=True, exist_ok=True)
    return root


def audit_log_path() -> Path:
    return ensure_state_dirs() / "audit-log.jsonl"


def collaboration_log_path() -> Path:
    return ensure_state_dirs() / "collaboration-log.json"


def quest_log_path() -> Path:
    return ensure_state_dirs() / "quest-log.json"


def quarantine_state_path() -> Path:
    return ensure_state_dirs() / "quarantine-state.json"


def accepted_risk_path() -> Path:
    return ensure_state_dirs() / "accepted-risk.json"


def inventory_cache_path() -> Path:
    return ensure_state_dirs() / "cache" / "inventory.json"


def self_check_cache_path() -> Path:
    return ensure_state_dirs() / "cache" / "self-checks.json"


def public_readiness_cache_path() -> Path:
    return ensure_state_dirs() / "cache" / "public-readiness.json"


def mitigation_cases_root() -> Path:
    root = ensure_state_dirs() / "cases"
    root.mkdir(parents=True, exist_ok=True)
    return root


def quarantine_artifacts_root() -> Path:
    root = ensure_state_dirs() / "quarantine"
    root.mkdir(parents=True, exist_ok=True)
    return root


def host_id() -> str:
    raw = (
        os.environ.get("COMPUTERNAME")
        or socket.gethostname()
        or "unknown-host"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
