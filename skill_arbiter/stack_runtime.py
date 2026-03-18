from __future__ import annotations

import copy
import ipaddress
import json
import os
import time
import urllib.error
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


STACK_HEALTH_URL_ENV = "STARFRAME_STACK_HEALTH_URL"
STACK_MODE_ENV = "SKILL_ARBITER_STACK_MODE"
POLL_PROFILE_ENV = "SKILL_ARBITER_STACK_POLL_PROFILE"
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

STACK_TIMEOUT_SECONDS = 2.0
STACK_RUNTIME_CACHE_SECONDS = 3.0

_STACK_RUNTIME_CACHE: dict[str, Any] = {
    "expires_at": 0.0,
    "payload": None,
}


_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _first_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return default


def _first_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def _first_dict(row: dict[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _pick_str(row: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = _first_str(row.get(key), "")
        if value:
            return value
    return default


def _pick_dict(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        candidate = row.get(key)
        if isinstance(candidate, dict):
            return candidate
    return {}


def _sanitize_path_hint(value: str) -> str:
    raw = _first_str(value, "")
    if not raw:
        return ""
    normalized = raw.replace("\\", "/").rstrip("/")
    if "/" not in normalized:
        return normalized[:120]
    leaf = normalized.split("/")[-1]
    return leaf[:120]


def stack_mode() -> str:
    mode = _first_str(os.environ.get(STACK_MODE_ENV), "lean").lower()
    return mode if mode in KNOWN_STACK_MODES else "lean"


def stack_health_url() -> str:
    return _first_str(os.environ.get(STACK_HEALTH_URL_ENV), "")


def _stack_health_target(url: str) -> str:
    normalized = _first_str(url, "")
    if not normalized:
        return ""
    parsed = urlparse(normalized)
    host = _first_str(parsed.hostname, "").lower()
    if not host:
        return "configured"
    if host in _LOOPBACK_HOSTS:
        return "loopback"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "private_network" if host.endswith(".local") else "external"
    if address.is_loopback:
        return "loopback"
    if address.is_private:
        return "private_network"
    return "external"


def stack_health_target() -> str:
    return _stack_health_target(stack_health_url())


def _default_profile() -> StackPollProfile:
    mode = stack_mode()
    return STACK_POLL_PROFILES.get(mode, STACK_POLL_PROFILES["lean"])


def load_poll_profile() -> dict[str, Any]:
    profile = _default_profile()
    selected = _first_str(os.environ.get(POLL_PROFILE_ENV), profile.name).lower()
    base = STACK_POLL_PROFILES.get(selected, profile)

    profile_override = {}
    for env_name, key in POLL_PROFILE_OVERRIDES.items():
        value = os.environ.get(env_name)
        if value is None:
            continue
        profile_override[key] = _first_int(value, getattr(base, key), minimum=10000)

    return {
        "name": selected,
        "health_ms": profile_override.get("health_ms", base.health_ms),
        "passive_inventory_ms": profile_override.get("passive_inventory_ms", base.passive_inventory_ms),
        "skill_game_ms": profile_override.get("skill_game_ms", base.skill_game_ms),
        "collaboration_ms": profile_override.get("collaboration_ms", base.collaboration_ms),
        "stack_runtime_ms": profile_override.get("stack_runtime_ms", base.stack_runtime_ms),
    }


def _normalize_last_seen(events: dict[str, Any] | list[dict[str, Any]]) -> str:
    if not events:
        return ""
    now = datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat()
    if isinstance(events, list):
        last = events[-1].get("created_at") if isinstance(events[-1], dict) else None
        return str(last or now)
    return now


def summarize_subagents_from_events(events: list[dict[str, Any]], *, max_items: int = 6) -> dict[str, Any]:
    counts = Counter()
    last_seen: dict[str, str] = {}
    filtered_count = 0
    ignored = {
        "",
        "local",
        "operator",
        "skill-arbiter",
        "skill_arbiter",
        "system",
        "skill-enforcer",
        "meshgpt-dcc",
        "meshgpt_admin",
        "meshgpt-admin",
    }

    for event in events or []:
        collaborators = event.get("collaborators")
        if not isinstance(collaborators, list):
            continue
        for name in collaborators:
            normalized = _first_str(name, "").lower()
            if not normalized or normalized in ignored:
                continue
            if normalized.startswith("skill-") and not normalized.startswith("subagent-"):
                continue
            counts[normalized] += 1
            if normalized not in last_seen and "created_at" in event:
                last_seen[normalized] = str(event.get("created_at", ""))
        filtered_count += 1

    active = []
    for name, count in counts.most_common(max_items):
        active.append(
            {
                "name": name,
                "event_count": int(count),
                "last_seen": last_seen.get(name, ""),
            },
        )

    return {
        "available": bool(active),
        "source": "collaboration_fallback",
        "active_subagents": active,
        "observed_event_count": int(filtered_count),
        "last_updated": _normalize_last_seen(events),
    }


def _parse_mx3_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    runtime = _first_dict(payload, ("mx3", "runtime", "runtime_state", "mx3_runtime", "shim"))
    active_sequence = (
        _pick_str(runtime, ("active_sequence_name", "active_sequence", "active_dfp", "dfp_sequence"), "")
        or _pick_str(payload, ("active_sequence_name", "active_sequence", "active_dfp", "dfp_sequence"), "")
    )
    active_dfp_path = (
        _pick_str(runtime, ("active_dfp_path", "dfp_path"), "")
        or _pick_str(payload, ("active_dfp_path", "dfp_path"), "")
    )
    mode = _pick_str(runtime, ("feeder_mode", "mode", "runtime_mode", "state"), "")
    if not mode:
        mode = "unknown"
    feeder_state = _pick_str(runtime, ("feeder_state", "feeder", "feeder_status"), "")
    if not feeder_state:
        feeder_state = "unknown"
    owner_job_id = _pick_str(runtime, ("owner_job_id", "job_id", "owner"), "")
    fallback_reason = _pick_str(runtime, ("fallback_reason", "failure_reason", "reason"), "")
    return {
        "available": bool(runtime),
        "mode": mode,
        "feeder_state": feeder_state,
        "owner_job_id": owner_job_id,
        "active_sequence_name": active_sequence,
        "active_dfp_path": _sanitize_path_hint(active_dfp_path),
        "fallback_reason": fallback_reason,
    }


def _parse_subagent_payload(payload: dict[str, Any]) -> dict[str, Any]:
    coordination = _pick_dict(
        payload,
        (
            "subagents",
            "subagent_coordination",
            "coordination",
            "agents",
        ),
    )
    if not coordination:
        return {
            "available": False,
            "source": "stack_payload",
            "active_subagents": [],
            "observed_event_count": 0,
            "last_updated": "",
        }

    raw_subagents = coordination.get("active") or coordination.get("agents")
    active: list[dict[str, str]] = []
    if isinstance(raw_subagents, list):
        for row in raw_subagents:
            if not isinstance(row, dict):
                continue
            name = _first_str(row.get("name"))
            if not name:
                continue
            active.append(
                {
                    "name": name,
                    "state": _pick_str(row, ("state", "status"), "active"),
                    "repo_scope": row.get("repo_scope") if isinstance(row.get("repo_scope"), list) else [],
                    "last_seen": _first_str(row.get("last_seen", "")),
                },
            )
    elif isinstance(raw_subagents, dict):
        for name, row in sorted(raw_subagents.items()):
            if not isinstance(row, dict):
                continue
            state = _pick_str(row, ("state", "status"), "active")
            active.append({"name": name, "state": state, "repo_scope": row.get("repo_scope", []), "last_seen": _first_str(row.get("last_seen", ""))})
    return {
        "available": True,
        "source": "stack_coordination",
        "active_subagents": active,
        "observed_event_count": int(coordination.get("observed_event_count", len(active))),
        "last_updated": _first_str(coordination.get("last_updated"), ""),
    }


def _normalize_stack_snapshot(payload: dict[str, Any], *, requested_mode: str, source: str) -> dict[str, Any]:
    mx3 = _parse_mx3_runtime(payload)
    status = _first_str(payload.get("status"), "")
    telemetry = _pick_dict(payload, ("telemetry", "runtime", "runtime_state"))
    provider_count = 0
    providers = telemetry.get("providers")
    if isinstance(providers, dict):
        provider_count = len(providers)
    routes = _pick_dict(payload, ("routing", "routes"))
    route_count = len(routes) if isinstance(routes, dict) else 0
    return {
        "available": True,
        "source": source,
        "stack_mode": requested_mode,
        "last_polled_at": datetime.now(timezone.utc).isoformat(),
        "requested_by": _first_str(payload.get("requested_by"), ""),
        "status": status or "unknown",
        "mx3": mx3,
        "providers": {
            "provider_count": provider_count,
            "route_count": route_count,
            "topology_exposed": False,
        },
        "subagent_coordination": _parse_subagent_payload(payload),
        "health": {
            "status": status or "unknown",
            "target": _stack_health_target(stack_health_url()),
        },
    }


def _fetch_stack_payload(url: str) -> dict[str, Any]:
    request = Request(f"{url.rstrip('/')}/api/health", method="GET")
    with urlopen(request, timeout=STACK_TIMEOUT_SECONDS) as response:  # nosec B310
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("stack health endpoint did not return JSON object")
    return payload


def stack_runtime_snapshot(
    *,
    fallback_events: list[dict[str, Any]] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    now = time.time()
    if not force_refresh:
        cached_payload = _STACK_RUNTIME_CACHE.get("payload")
        cached_until = _STACK_RUNTIME_CACHE.get("expires_at", 0.0)
        if cached_payload is not None and cached_until > now:
            return copy.deepcopy(cached_payload)

    requested_mode = stack_mode()
    url = stack_health_url()
    fallback = {
        "available": False,
        "source": "stack_endpoint",
        "stack_mode": requested_mode,
        "last_polled_at": datetime.now(timezone.utc).isoformat(),
        "status": "unavailable",
        "mx3": {
            "available": False,
            "mode": "unknown",
            "feeder_state": "unknown",
            "owner_job_id": "",
            "active_sequence_name": "",
            "active_dfp_path": "",
            "fallback_reason": "stack health endpoint not configured",
        },
        "providers": {
            "provider_count": 0,
            "route_count": 0,
            "topology_exposed": False,
        },
        "subagent_coordination": summarize_subagents_from_events(
            fallback_events or [],
            max_items=6,
        )
        if fallback_events is not None
        else {
            "available": False,
            "source": "stack_endpoint",
            "active_subagents": [],
            "observed_event_count": 0,
            "last_updated": "",
        },
        "health": {
            "status": "unavailable",
            "target": "",
        },
    }

    if not url:
        if fallback_events:
            fallback["mx3"] = normalize_mx3_from_events(fallback_events)
            if "fallback_reason" in fallback["mx3"]:
                fallback["fallback_reason"] = fallback["mx3"]["fallback_reason"]
        _STACK_RUNTIME_CACHE["expires_at"] = now + STACK_RUNTIME_CACHE_SECONDS
        _STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(fallback)
        return fallback
    try:
        payload = _fetch_stack_payload(url)
        normalized = _normalize_stack_snapshot(payload, requested_mode=requested_mode, source="stack_health")
        ttl = max(1.0, load_poll_profile().get("stack_runtime_ms", 30000) / 1000.0)
        cache_ttl = min(max(ttl * 0.75, 1.0), STACK_RUNTIME_CACHE_SECONDS)
        _STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(normalized)
        _STACK_RUNTIME_CACHE["expires_at"] = now + cache_ttl
        return normalized
    except (OSError, ValueError, urllib.error.URLError) as exc:
        fallback["health"]["status"] = "error"
        fallback["health"]["target"] = _stack_health_target(url)
        fallback["health"]["error"] = exc.__class__.__name__
        if fallback_events:
            fallback["subagent_coordination"] = summarize_subagents_from_events(fallback_events, max_items=6)
            fallback["mx3"] = normalize_mx3_from_events(fallback_events)
            fallback["fallback_reason"] = "stack endpoint unavailable"
        _STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(fallback)
        _STACK_RUNTIME_CACHE["expires_at"] = now + STACK_RUNTIME_CACHE_SECONDS
        return fallback


def normalize_mx3_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    events = events or []
    for event in reversed(events[-min(len(events), 8):]):
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        candidate = {
            "available": True,
            "mode": _pick_str(metadata, ("mx3_mode", "runtime_mode", "feeder_mode")),
            "feeder_state": _pick_str(metadata, ("mx3_feeder_state", "feeder_state", "feeder_status")),
            "owner_job_id": _pick_str(metadata, ("mx3_owner_job_id", "owner_job_id", "job_id")),
            "active_sequence_name": _pick_str(metadata, ("mx3_active_sequence_name", "active_sequence_name", "active_sequence")),
            "active_dfp_path": _sanitize_path_hint(_pick_str(metadata, ("mx3_active_dfp_path", "active_dfp_path", "dfp_path"))),
            "fallback_reason": _pick_str(metadata, ("mx3_fallback_reason", "fallback_reason")),
        }
        candidate["mode"] = candidate["mode"] or "unknown"
        candidate["feeder_state"] = candidate["feeder_state"] or "unknown"
        candidate["fallback_reason"] = candidate["fallback_reason"] or "subagent-based inference (stack endpoint unavailable)"
        return candidate
    return {
        "available": bool(events),
        "mode": "unknown",
        "feeder_state": "unknown",
        "owner_job_id": "",
        "active_sequence_name": "",
        "active_dfp_path": "",
        "fallback_reason": (
            "subagent-based inference (stack endpoint unavailable)" if events else "no stack endpoint and no collaboration signal"
        ),
    }
