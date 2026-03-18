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


def advisor_model(refresh: bool = False) -> str:
    configured = _default_model().strip()
    if configured and configured.lower() not in {"auto", "preferred", "default"}:
        return configured
    available = available_models(refresh=refresh)
    if not available:
        return os.environ.get("STARFRAME_SHARED_AGENT_MODEL", "radeon-qwen3.5-4b").strip() or "radeon-qwen3.5-4b"
    return _select_model(available)


def advisor_base_url() -> str:
    return _default_base_url()


def advisor_status(timeout_s: float = 0.4) -> dict[str, str]:
    base_url = _default_base_url()
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
            return {"status": "online", "detail": f"reachable at {host}:{port}; model={model}"}
    except OSError:
        return {"status": "offline", "detail": f"unreachable at {host}:{port}"}


@lru_cache(maxsize=1)
def _cached_available_models() -> tuple[str, ...]:
    base_url = _default_base_url()
    if not enabled() or not _local_only(base_url):
        return ()
    req = request.Request(f"{base_url}/models", headers={"Content-Type": "application/json"}, method="GET")
    try:
        with request.urlopen(req, timeout=1.0) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, error.HTTPError, TimeoutError, socket.timeout, json.JSONDecodeError):
        return ()
    rows = body.get("data") or []
    models = []
    for row in rows:
        model_id = str(row.get("id") or "").strip()
        if model_id:
            models.append(model_id)
    return tuple(models)


def available_models(refresh: bool = False) -> list[str]:
    if refresh:
        _cached_available_models.cache_clear()
    return list(_cached_available_models())


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
    base_url = _default_base_url()
    if not enabled() or not _local_only(base_url):
        return ""
    model_id = advisor_model()
    prompt = (
        "You are the NullClaw local security advisor. "
        "Respond in 2 short sentences. Focus on coding-agent/skill security and next host-safe action.\n"
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
