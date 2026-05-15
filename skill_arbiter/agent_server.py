from __future__ import annotations

# ruff: noqa: F401

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .about import about_payload
from .accepted_risk import accept_subject, revoke_subject
from .agent_http import _json_response, _origin_allowed, _requested_origin, _resolve_allowed_origin, _write_cors_headers
from .agent_routes import handle_get, handle_post
from .agent_state import NullClawStateBase
from .audit_log import append_audit_event, read_audit_events
from .collaboration import (
    read_collaboration_events,
    record_payload as record_collaboration_payload,
    status_payload as collaboration_status_payload,
)
from .contracts import AuditEvent, IncidentRecord, PolicyDecision
from .inventory import build_inventory_snapshot, load_cached_inventory
from .llm_advisor import advisor_base_url, advisor_model, advisor_status, enabled as advisor_enabled
from .mitigation import execute_case_action, list_cases, plan_case, reconcile_cases
from .paths import (
    DEFAULT_AGENT_HOST,
    DEFAULT_AGENT_PORT,
    DEFAULT_CANDIDATES_ROOT,
    DEFAULT_SKILLS_ROOT,
    REPO_ROOT,
    collaboration_log_path,
    host_id,
    inventory_cache_path,
    quest_log_path,
    self_check_cache_path,
)
from .privacy_policy import scan_repo
from .public_readiness import load_cached_public_readiness, run_public_readiness_scan
from .quest_runtime import record_payload as record_quest_payload, status_payload as quest_status_payload
from .quarantine import apply_quarantine, confirm_delete_skill, confirm_kill_process, release_quarantine
from .self_governance import run_self_governance_scan
from .skill_game_runtime import record_payload as record_skill_game_payload, status_payload as skill_game_status_payload
from .stack_runtime import load_poll_profile, stack_runtime_snapshot
from supply_chain_guard import scan_skill_dir_content, scan_skill_tree, summarize_findings


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
