from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import Any


STACK_HEALTH_URL_ENV = "STARFRAME_STACK_HEALTH_URL"
STACK_MODE_ENV = "SKILL_ARBITER_STACK_MODE"
POLL_PROFILE_ENV = "SKILL_ARBITER_STACK_POLL_PROFILE"
ENABLE_CODEX_WATCH_ENV = "SKILL_ARBITER_ENABLE_CODEX_WATCH"
POLL_PROFILE_OVERRIDES = {
    "SKILL_ARBITER_STACK_HEALTH_MS": "health_ms",
    "SKILL_ARBITER_STACK_PASSIVE_INVENTORY_MS": "passive_inventory_ms",
    "SKILL_ARBITER_STACK_SKILL_GAME_MS": "skill_game_ms",
    "SKILL_ARBITER_STACK_COLLAB_MS": "collaboration_ms",
    "SKILL_ARBITER_STACK_RUNTIME_MS": "stack_runtime_ms",
}


@dataclass(frozen=True)
class StackPollProfile:
    name: str
    health_ms: int
    passive_inventory_ms: int
    skill_game_ms: int
    collaboration_ms: int
    stack_runtime_ms: int


KNOWN_STACK_MODES = {"lean", "balanced", "full"}

STACK_POLL_PROFILES: dict[str, StackPollProfile] = {
    "lean": StackPollProfile(
        name="lean",
        health_ms=30000,
        passive_inventory_ms=180000,
        skill_game_ms=120000,
        collaboration_ms=120000,
        stack_runtime_ms=60000,
    ),
    "balanced": StackPollProfile(
        name="balanced",
        health_ms=20000,
        passive_inventory_ms=120000,
        skill_game_ms=90000,
        collaboration_ms=90000,
        stack_runtime_ms=45000,
    ),
    "full": StackPollProfile(
        name="full",
        health_ms=10000,
        passive_inventory_ms=60000,
        skill_game_ms=45000,
        collaboration_ms=60000,
        stack_runtime_ms=30000,
    ),
}


def stack_mode(module: ModuleType) -> str:
    mode = module._first_str(module.os.environ.get(module.STACK_MODE_ENV), "lean").lower()
    return mode if mode in module.KNOWN_STACK_MODES else "lean"


def stack_health_url(module: ModuleType) -> str:
    return module._first_str(module.os.environ.get(module.STACK_HEALTH_URL_ENV), "")


def _default_profile(module: ModuleType) -> StackPollProfile:
    mode = stack_mode(module)
    return module.STACK_POLL_PROFILES.get(mode, module.STACK_POLL_PROFILES["lean"])


def load_poll_profile(module: ModuleType) -> dict[str, Any]:
    profile = _default_profile(module)
    selected = module._first_str(module.os.environ.get(module.POLL_PROFILE_ENV), profile.name).lower()
    base = module.STACK_POLL_PROFILES.get(selected, profile)

    profile_override = {}
    for env_name, key in module.POLL_PROFILE_OVERRIDES.items():
        value = module.os.environ.get(env_name)
        if value is None:
            continue
        profile_override[key] = module._first_int(value, getattr(base, key), minimum=10000)

    return {
        "name": selected,
        "health_ms": profile_override.get("health_ms", base.health_ms),
        "passive_inventory_ms": profile_override.get("passive_inventory_ms", base.passive_inventory_ms),
        "skill_game_ms": profile_override.get("skill_game_ms", base.skill_game_ms),
        "collaboration_ms": profile_override.get("collaboration_ms", base.collaboration_ms),
        "stack_runtime_ms": profile_override.get("stack_runtime_ms", base.stack_runtime_ms),
    }
