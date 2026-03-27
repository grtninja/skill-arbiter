from __future__ import annotations

import json
import os
import socket
from functools import lru_cache
from urllib import error, parse, request


def _local_only(url_text: str) -> bool:
    parsed = parse.urlparse(url_text)
    hostname = (parsed.hostname or "").lower()
    return hostname in {"127.0.0.1", "localhost", "::1"}


def _default_base_url() -> str:
    return os.environ.get(
        "NULLCLAW_AGENT_BASE_URL",
        os.environ.get("STARFRAME_SHARED_AGENT_BASE_URL", "http://127.0.0.1:9000/v1"),
    ).rstrip("/")


def _default_model() -> str:
    return os.environ.get(
        "NULLCLAW_AGENT_MODEL",
        os.environ.get(
            "STARFRAME_SHARED_AGENT_MODEL",
            os.environ.get("MX3_LMSTUDIO_TOOL_MODEL", "radeon-qwen3.5-4b"),
        ),
    )


def enabled() -> bool:
    return os.environ.get("NULLCLAW_AGENT_ENABLE_LLM", "1").strip().lower() not in {"0", "false", "no"}


def _candidate_base_urls() -> list[str]:
    configured = [
        _default_base_url(),
        os.environ.get("MX3_SHARED_AGENT_BASE_URL", "").rstrip("/"),
        os.environ.get("LMSTUDIO_BASE_URL", "").rstrip("/"),
    ]
    fallbacks = [
        "http://127.0.0.1:9000/v1",
        "http://127.0.0.1:2244/v1",
        "http://127.0.0.1:2235/v1",
        "http://127.0.0.1:2234/v1",
        "http://127.0.0.1:1234/v1",
    ]
    ordered: list[str] = []
    for item in [*configured, *fallbacks]:
        text = str(item or "").strip().rstrip("/")
        if not text or not _local_only(text) or text in ordered:
            continue
        ordered.append(text)
    return ordered


def _fetch_models(base_url: str, timeout_s: float = 1.5) -> list[str]:
    req = request.Request(f"{base_url}/models", headers={"Content-Type": "application/json"}, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_s) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, error.HTTPError, TimeoutError, socket.timeout, json.JSONDecodeError):
        return []
    rows = body.get("data") or []
    models: list[str] = []
    for row in rows:
        model_id = str(row.get("id") or "").strip()
        if model_id:
            models.append(model_id)
    return models


def _endpoint_reachable(base_url: str, timeout_s: float = 0.2) -> bool:
    parsed = parse.urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


@lru_cache(maxsize=8)
def _resolved_advisor_target(candidate_urls: tuple[str, ...], enabled_flag: bool) -> tuple[str, tuple[str, ...]]:
    if not enabled_flag:
        return ("", ())
    for base_url in candidate_urls:
        if not _endpoint_reachable(base_url):
            continue
        models = _fetch_models(base_url, timeout_s=0.8)
        if models:
            return (base_url, tuple(models))
    fallback = _default_base_url()
    if enabled() and _local_only(fallback) and _endpoint_reachable(fallback):
        return (fallback, ())
    return ("", ())


def advisor_model(refresh: bool = False) -> str:
    configured = _default_model().strip()
    if refresh:
        _base_url, available = _resolve_target(refresh=True)
    else:
        available = available_models(refresh=False)
    if configured and configured.lower() not in {"auto", "preferred", "default"}:
        if not available or configured in available:
            return configured
        return _select_model(available)
    if not available:
        return os.environ.get("STARFRAME_SHARED_AGENT_MODEL", "radeon-qwen3.5-4b").strip() or "radeon-qwen3.5-4b"
    return _select_model(available)


def advisor_base_url() -> str:
    base_url, _models = _resolve_target(refresh=False)
    return base_url or _default_base_url()


def _resolve_target(refresh: bool = False) -> tuple[str, tuple[str, ...]]:
    if refresh:
        _resolved_advisor_target.cache_clear()
        _cached_available_models.cache_clear()
    candidate_urls = tuple(_candidate_base_urls())
    return _resolved_advisor_target(candidate_urls, enabled())


def advisor_status(timeout_s: float = 0.4) -> dict[str, str]:
    base_url, models = _resolve_target(refresh=False)
    if not enabled():
        return {"status": "disabled", "detail": "advisor disabled by env"}
    if not _local_only(base_url):
        return {"status": "blocked", "detail": "advisor base URL must remain loopback-local"}
    parsed = parse.urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            model = advisor_model(refresh=True)
            model_count = len(models or ())
            return {"status": "online", "detail": f"reachable at {host}:{port}; model={model}; visible_models={model_count}"}
    except OSError:
        return {"status": "offline", "detail": f"unreachable at {host}:{port}"}


@lru_cache(maxsize=8)
def _cached_available_models(candidate_urls: tuple[str, ...], enabled_flag: bool) -> tuple[str, ...]:
    _base_url, models = _resolved_advisor_target(candidate_urls, enabled_flag)
    return models


def available_models(refresh: bool = False) -> list[str]:
    if refresh:
        _cached_available_models.cache_clear()
    candidate_urls = tuple(_candidate_base_urls())
    return list(_cached_available_models(candidate_urls, enabled()))


def _model_score(model_id: str) -> tuple[int, int, int, str]:
    lowered = model_id.lower()
    qwen = 1 if "qwen" in lowered else 0
    coder = 1 if "coder" in lowered or "code" in lowered else 0
    small = 1 if any(token in lowered for token in ("3b", "4b", "7b", "mini", "small", "turbo")) else 0
    return (-qwen, -coder, -small, lowered)


def _select_model(models: list[str]) -> str:
    ranked = sorted(models, key=_model_score)
    if ranked:
        return ranked[0]
    return os.environ.get("STARFRAME_SHARED_AGENT_MODEL", "radeon-qwen3.5-4b").strip() or "radeon-qwen3.5-4b"


def request_local_advice(subject: str, findings: list[str], timeout_s: float = 4.0) -> str:
    base_url, available = _resolve_target(refresh=True)
    if not enabled() or not _local_only(base_url):
        return ""
    model_id = advisor_model(refresh=not bool(available))
    prompt = (
        "You are the NullClaw local security advisor. "
        "Respond in 2 short sentences. Focus on coding-agent/skill security, current operator progress, and next host-safe action.\n"
        f"Subject: {subject}\n"
        f"Findings: {', '.join(findings[:12])}\n"
    )
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a fast local coding-security assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 120,
    }
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_s) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, error.HTTPError, TimeoutError, socket.timeout, json.JSONDecodeError):
        return ""
    choices = body.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "").strip()[:500]
