from __future__ import annotations

import copy
from datetime import datetime, timezone
from types import ModuleType
from typing import Any


def _stack_health_target(module: ModuleType, url: str) -> str:
    normalized = module._first_str(url, "")
    if not normalized:
        return ""
    parsed = module.urlparse(normalized)
    host = module._first_str(parsed.hostname, "").lower()
    if not host:
        return "configured"
    if host in module._LOOPBACK_HOSTS:
        return "loopback"
    try:
        address = module.ipaddress.ip_address(host)
    except ValueError:
        return "private_network" if host.endswith(".local") else "external"
    if address.is_loopback:
        return "loopback"
    if address.is_private:
        return "private_network"
    return "external"


def stack_health_target(module: ModuleType) -> str:
    return _stack_health_target(module, module.stack_health_url())


def _normalize_last_seen(module: ModuleType, events: dict[str, Any] | list[dict[str, Any]]) -> str:
    if not events:
        return ""
    now = datetime.fromtimestamp(module.time.time(), tz=timezone.utc).isoformat()
    if isinstance(events, list):
        last = events[-1].get("created_at") if isinstance(events[-1], dict) else None
        return str(last or now)
    return now


def summarize_subagents_from_events(module: ModuleType, events: list[dict[str, Any]], *, max_items: int = 6) -> dict[str, Any]:
    counts = module.Counter()
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
            normalized = module._first_str(name, "").lower()
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
            }
        )
    return {
        "available": bool(active),
        "source": "collaboration_fallback",
        "active_subagents": active,
        "observed_event_count": int(filtered_count),
        "last_updated": _normalize_last_seen(module, events),
    }


def _parse_mx3_runtime(module: ModuleType, payload: dict[str, Any]) -> dict[str, Any]:
    runtime = module._first_dict(payload, ("mx3", "runtime", "runtime_state", "mx3_runtime", "shim"))
    active_sequence = (
        module._pick_str(runtime, ("active_sequence_name", "active_sequence", "active_dfp", "dfp_sequence"), "")
        or module._pick_str(payload, ("active_sequence_name", "active_sequence", "active_dfp", "dfp_sequence"), "")
    )
    active_dfp_path = (
        module._pick_str(runtime, ("active_dfp_path", "dfp_path"), "")
        or module._pick_str(payload, ("active_dfp_path", "dfp_path"), "")
    )
    mode = module._pick_str(runtime, ("feeder_mode", "mode", "runtime_mode", "state"), "") or "unknown"
    feeder_state = module._pick_str(runtime, ("feeder_state", "feeder", "feeder_status"), "") or "unknown"
    owner_job_id = module._pick_str(runtime, ("owner_job_id", "job_id", "owner"), "")
    fallback_reason = module._pick_str(runtime, ("fallback_reason", "failure_reason", "reason"), "")
    return {
        "available": bool(runtime),
        "mode": mode,
        "feeder_state": feeder_state,
        "owner_job_id": owner_job_id,
        "active_sequence_name": active_sequence,
        "active_dfp_path": module._sanitize_path_hint(active_dfp_path),
        "fallback_reason": fallback_reason,
    }


def _parse_subagent_payload(module: ModuleType, payload: dict[str, Any]) -> dict[str, Any]:
    coordination = module._pick_dict(
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
    active: list[dict[str, Any]] = []
    if isinstance(raw_subagents, list):
        for row in raw_subagents:
            if not isinstance(row, dict):
                continue
            name = module._first_str(row.get("name"))
            if not name:
                continue
            active.append(
                {
                    "name": name,
                    "state": module._pick_str(row, ("state", "status"), "active"),
                    "repo_scope": row.get("repo_scope") if isinstance(row.get("repo_scope"), list) else [],
                    "last_seen": module._first_str(row.get("last_seen", "")),
                }
            )
    elif isinstance(raw_subagents, dict):
        for name, row in sorted(raw_subagents.items()):
            if not isinstance(row, dict):
                continue
            active.append(
                {
                    "name": name,
                    "state": module._pick_str(row, ("state", "status"), "active"),
                    "repo_scope": row.get("repo_scope", []),
                    "last_seen": module._first_str(row.get("last_seen", "")),
                }
            )
    return {
        "available": True,
        "source": "stack_coordination",
        "active_subagents": active,
        "observed_event_count": int(coordination.get("observed_event_count", len(active))),
        "last_updated": module._first_str(coordination.get("last_updated"), ""),
    }


def _normalize_stack_snapshot(module: ModuleType, payload: dict[str, Any], *, requested_mode: str, source: str) -> dict[str, Any]:
    mx3 = module._parse_mx3_runtime(payload)
    status = module._first_str(payload.get("status"), "")
    telemetry = module._pick_dict(payload, ("telemetry", "runtime", "runtime_state"))
    provider_count = 0
    providers = telemetry.get("providers")
    if isinstance(providers, dict):
        provider_count = len(providers)
    routes = module._pick_dict(payload, ("routing", "routes"))
    route_count = len(routes) if isinstance(routes, dict) else 0
    return {
        "available": True,
        "source": source,
        "stack_mode": requested_mode,
        "last_polled_at": datetime.now(timezone.utc).isoformat(),
        "requested_by": module._first_str(payload.get("requested_by"), ""),
        "status": status or "unknown",
        "mx3": mx3,
        "providers": {
            "provider_count": provider_count,
            "route_count": route_count,
            "topology_exposed": False,
        },
        "subagent_coordination": module._parse_subagent_payload(payload),
        "health": {
            "status": status or "unknown",
            "target": module._stack_health_target(module.stack_health_url()),
        },
        "local_supervision": module._local_supervision_snapshot(),
    }


def _fetch_stack_payload(module: ModuleType, url: str) -> dict[str, Any]:
    request = module.Request(f"{url.rstrip('/')}/api/health", method="GET")
    with module.urlopen(request, timeout=module.STACK_TIMEOUT_SECONDS) as response:  # nosec B310
        payload = module.json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("stack health endpoint did not return JSON object")
    return payload


def stack_runtime_snapshot(
    module: ModuleType,
    *,
    fallback_events: list[dict[str, Any]] | None = None,
    force_refresh: bool = False,
    refresh_local_supervision: bool = False,
) -> dict[str, Any]:
    now = module.time.time()
    if not force_refresh:
        cached_payload = module._STACK_RUNTIME_CACHE.get("payload")
        cached_until = module._STACK_RUNTIME_CACHE.get("expires_at", 0.0)
        if cached_payload is not None and cached_until > now:
            return copy.deepcopy(cached_payload)

    requested_mode = module.stack_mode()
    url = module.stack_health_url()
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
        "subagent_coordination": module.summarize_subagents_from_events(fallback_events or [], max_items=6)
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
        "local_supervision": module._local_supervision_snapshot(
            refresh=refresh_local_supervision,
            include_advisor_note=refresh_local_supervision,
        ),
    }
    if not url:
        if fallback_events:
            fallback["mx3"] = module.normalize_mx3_from_events(fallback_events)
            if "fallback_reason" in fallback["mx3"]:
                fallback["fallback_reason"] = fallback["mx3"]["fallback_reason"]
        module._STACK_RUNTIME_CACHE["expires_at"] = now + module.STACK_RUNTIME_CACHE_SECONDS
        module._STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(fallback)
        return fallback
    try:
        payload = module._fetch_stack_payload(url)
        normalized = module._normalize_stack_snapshot(payload, requested_mode=requested_mode, source="stack_health")
        normalized["local_supervision"] = module._local_supervision_snapshot(
            refresh=refresh_local_supervision,
            include_advisor_note=refresh_local_supervision,
        )
        ttl = max(1.0, module.load_poll_profile().get("stack_runtime_ms", 30000) / 1000.0)
        cache_ttl = max(module.STACK_RUNTIME_CACHE_SECONDS, min(ttl * 0.75, 15.0))
        module._STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(normalized)
        module._STACK_RUNTIME_CACHE["expires_at"] = now + cache_ttl
        return normalized
    except (OSError, ValueError, module.urllib.error.URLError) as exc:
        fallback["health"]["status"] = "error"
        fallback["health"]["target"] = module._stack_health_target(url)
        fallback["health"]["error"] = exc.__class__.__name__
        if fallback_events:
            fallback["subagent_coordination"] = module.summarize_subagents_from_events(fallback_events, max_items=6)
            fallback["mx3"] = module.normalize_mx3_from_events(fallback_events)
            fallback["fallback_reason"] = "stack endpoint unavailable"
        module._STACK_RUNTIME_CACHE["payload"] = copy.deepcopy(fallback)
        module._STACK_RUNTIME_CACHE["expires_at"] = now + module.STACK_RUNTIME_CACHE_SECONDS
        return fallback


def normalize_mx3_from_events(module: ModuleType, events: list[dict[str, Any]]) -> dict[str, Any]:
    events = events or []
    for event in reversed(events[-min(len(events), 8) :]):
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        candidate = {
            "available": True,
            "mode": module._pick_str(metadata, ("mx3_mode", "runtime_mode", "feeder_mode")),
            "feeder_state": module._pick_str(metadata, ("mx3_feeder_state", "feeder_state", "feeder_status")),
            "owner_job_id": module._pick_str(metadata, ("mx3_owner_job_id", "owner_job_id", "job_id")),
            "active_sequence_name": module._pick_str(metadata, ("mx3_active_sequence_name", "active_sequence_name", "active_sequence")),
            "active_dfp_path": module._sanitize_path_hint(module._pick_str(metadata, ("mx3_active_dfp_path", "active_dfp_path", "dfp_path"))),
            "fallback_reason": module._pick_str(metadata, ("mx3_fallback_reason", "fallback_reason")),
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
