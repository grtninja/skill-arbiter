from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse


_LOOPBACK_ORIGIN_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _requested_origin(handler: BaseHTTPRequestHandler) -> str:
    return str(handler.headers.get("Origin", "")).strip()


def _resolve_allowed_origin(origin: str) -> str:
    requested = str(origin or "").strip()
    if not requested:
        return ""
    parsed = urlparse(requested)
    host = str(parsed.hostname or "").strip().lower()
    if parsed.scheme in {"http", "https"} and host in _LOOPBACK_ORIGIN_HOSTS:
        return requested
    return ""


def _origin_allowed(handler: BaseHTTPRequestHandler) -> bool:
    origin = _requested_origin(handler)
    if not origin:
        return True
    return bool(_resolve_allowed_origin(origin))


def _write_cors_headers(handler: BaseHTTPRequestHandler) -> None:
    allowed_origin = _resolve_allowed_origin(_requested_origin(handler))
    if allowed_origin:
        handler.send_header("Access-Control-Allow-Origin", allowed_origin)
        handler.send_header("Access-Control-Allow-Headers", "Content-Type")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        handler.send_header("Access-Control-Allow-Private-Network", "true")
        handler.send_header("Vary", "Origin")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    _write_cors_headers(handler)
    handler.send_header("Cache-Control", "no-store, max-age=0")
    handler.send_header("Pragma", "no-cache")
    handler.send_header("Expires", "0")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    try:
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        return
