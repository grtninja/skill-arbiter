from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .agent_http import _json_response, _origin_allowed, _write_cors_headers
from .agent_routes import handle_get, handle_post
from .agent_state import NullClawStateBase
from .paths import DEFAULT_AGENT_HOST, DEFAULT_AGENT_PORT


class NullClawState(NullClawStateBase):
    def __init__(self, skills_root: Path | None = None, candidate_root: Path | None = None) -> None:
        super().__init__(sys.modules[__name__], skills_root=skills_root, candidate_root=candidate_root)


def build_handler(state: NullClawState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_OPTIONS(self) -> None:
            if not _origin_allowed(self):
                _json_response(self, HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            _write_cors_headers(self)
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def do_GET(self) -> None:
            if not _origin_allowed(self):
                _json_response(self, HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            status, payload = handle_get(sys.modules[__name__], state, self.path)
            _json_response(self, status, payload)

        def do_POST(self) -> None:
            if not _origin_allowed(self):
                _json_response(self, HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            try:
                payload = self._read_json()
            except json.JSONDecodeError as exc:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            try:
                status, body = handle_post(sys.modules[__name__], state, self.path, payload)
                _json_response(self, status, body)
            except (ValueError, FileNotFoundError, OSError) as exc:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    return Handler


def run_agent(
    host: str = DEFAULT_AGENT_HOST,
    port: int = DEFAULT_AGENT_PORT,
    skills_root: Path | None = None,
    candidate_root: Path | None = None,
) -> None:
    state = NullClawState(skills_root=skills_root, candidate_root=candidate_root)
    server = ThreadingHTTPServer((host, port), build_handler(state))
    try:
        server.serve_forever()
    finally:
        server.server_close()
