from __future__ import annotations

import re
from pathlib import Path

from .llm_advisor import advisor_base_url, advisor_model, advisor_status, available_models, enabled as advisor_enabled
from .paths import REPO_ROOT
from . import stack_runtime


VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _project_version() -> str:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return "0.0.0"
    text = pyproject.read_text(encoding="utf-8", errors="ignore")
    match = VERSION_RE.search(text)
    return match.group(1) if match else "0.0.0"


def about_payload(host_id: str) -> dict[str, object]:
    advisor = advisor_status()
    poll_profile = stack_runtime.load_poll_profile()
    return {
        "application": "Skill Arbiter Security Console",
        "description": (
            "Windows-first NullClaw host security console for local skill governance, "
            "curated-source discovery, guarded threat suppression, and self-governance."
        ),
        "developer": "grtninja",
        "creator": "Edward A. Silvia",
        "email": "grtninja@hotmail.com",
        "version": _project_version(),
        "license": "MIT",
        "host_id": host_id,
        "repo_url": "https://github.com/grtninja/skill-arbiter",
        "issues_url": "https://github.com/grtninja/skill-arbiter/issues",
        "security_url": "https://github.com/grtninja/skill-arbiter/security",
        "support_url": "https://www.patreon.com/cw/grtninja",
        "posts_url": "https://www.patreon.com/grtninja/posts",
        "public_shape_note": (
            "Repo-tracked docs and generated artifacts must remain public-shape only. "
            "Local evidence, usernames, host-specific paths, and destructive-action records stay ignored."
        ),
        "stack_runtime_contract": {
            "stack_mode": stack_runtime.stack_mode(),
            "stack_health_url": stack_runtime.stack_health_target(),
            "poll_profile": poll_profile,
            "mx3_contract": {
                "required_visibility": [
                    "active_sequence_name",
                    "active_dfp_path",
                    "mode",
                    "feeder_state",
                    "owner_job_id",
                ],
            },
            "subagent_contract": {
                "source_priority": ["stack_endpoint", "collaboration_fallback"],
                "fields": ["name", "event_count", "state", "repo_scope", "last_seen"],
            },
        },
        "advisor": {
            "enabled": advisor_enabled(),
            "model": advisor_model(),
            "base_url": advisor_base_url(),
            "mode": "local_only",
            "selection_policy": "shared loopback Qwen agent lane by default; operator override only for specialized lanes",
            "available_models": available_models(),
            "status": advisor["status"],
            "detail": advisor["detail"],
        },
        "icon_png": "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.png",
        "icon_ico": "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.ico",
        "support_channels": [
            {"label": "GitHub Repo", "value": "https://github.com/grtninja/skill-arbiter"},
            {"label": "GitHub Issues", "value": "https://github.com/grtninja/skill-arbiter/issues"},
            {"label": "Security", "value": "https://github.com/grtninja/skill-arbiter/security"},
            {"label": "Patreon", "value": "https://www.patreon.com/cw/grtninja"},
        ],
    }
