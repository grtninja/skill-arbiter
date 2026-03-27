from __future__ import annotations

import json
import copy
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .about import about_payload
from .accepted_risk import accept_subject, revoke_subject
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
from .paths import DEFAULT_AGENT_HOST, DEFAULT_AGENT_PORT, DEFAULT_CANDIDATES_ROOT, DEFAULT_SKILLS_ROOT, REPO_ROOT, collaboration_log_path, host_id, inventory_cache_path, self_check_cache_path
from .privacy_policy import scan_repo
from .public_readiness import load_cached_public_readiness, run_public_readiness_scan
from .quarantine import apply_quarantine, confirm_delete_skill, confirm_kill_process, release_quarantine
from .self_governance import run_self_governance_scan
from .skill_game_runtime import record_payload as record_skill_game_payload, status_payload as skill_game_status_payload
from .stack_runtime import load_poll_profile, stack_runtime_snapshot
from supply_chain_guard import scan_skill_dir_content, scan_skill_tree, summarize_findings


class NullClawState:
    def __init__(self, skills_root: Path | None = None, candidate_root: Path | None = None) -> None:
        self.skills_root = skills_root or DEFAULT_SKILLS_ROOT
        self.candidate_root = candidate_root or DEFAULT_CANDIDATES_ROOT
        self.host_id = host_id()
        self._inventory_refresh_lock = threading.Lock()
        self._inventory_refresh_cache: dict[str, Any] = {
            "expires_at": 0.0,
            "payload": None,
        }

    def _candidate_root_label(self) -> str:
        try:
            return str(self.candidate_root.relative_to(REPO_ROOT))
        except ValueError:
            return "<external-candidate-root>"

    def health(self) -> dict[str, object]:
        about = about_payload(self.host_id)
        advisor = advisor_status()
        collaboration_events = (
            read_collaboration_events(limit=200)
            if not about.get("stack_runtime_contract", {}).get("stack_health_url", "")
            else None
        )
        return {
            "status": "ok",
            "service": "nullclaw-agent",
            "application": about["application"],
            "version": about["version"],
            "host_id": self.host_id,
            "policy_mode": "guarded_auto",
            "skills_root": "$CODEX_HOME/skills",
            "candidate_root": self._candidate_root_label(),
            "inventory_ready": inventory_cache_path().is_file(),
            "self_checks_ready": self_check_cache_path().is_file(),
            "collaboration_ready": collaboration_log_path().is_file(),
            "advisor_enabled": advisor_enabled(),
            "advisor_model": advisor_model(),
            "advisor_base_url": advisor_base_url(),
            "advisor_status": advisor["status"],
            "advisor_detail": advisor["detail"],
            "stack_mode": about.get("stack_runtime_contract", {}).get("stack_mode", ""),
            "stack_health_url": about.get("stack_runtime_contract", {}).get("stack_health_url", ""),
            "stack_runtime": stack_runtime_snapshot(fallback_events=collaboration_events),
            "poll_profile": load_poll_profile(),
        }

    def load_self_checks(self) -> dict[str, object]:
        path = self_check_cache_path()
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def run_self_checks(self) -> dict[str, object]:
        privacy = scan_repo(REPO_ROOT)
        governance = run_self_governance_scan(REPO_ROOT)
        payload = {
            "host_id": self.host_id,
            "privacy_passed": privacy.passed,
            "privacy_findings": [item.to_dict() for item in privacy.findings],
            "self_governance": governance,
        }
        self_check_cache_path().write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        append_audit_event(
            AuditEvent(
                event_type="self_checks_run",
                subject="repo",
                detail="ran privacy and self-governance checks",
                host_id=self.host_id,
                evidence_codes=[item.kind for item in privacy.findings[:6]],
            )
        )
        return payload

    def inventory_refresh(self, *, force: bool = False) -> dict[str, object]:
        now = time.time()
        if not force:
            with self._inventory_refresh_lock:
                cached = self._inventory_refresh_cache.get("payload")
                if self._inventory_refresh_cache["expires_at"] > now and cached is not None:
                    payload = copy.deepcopy(cached)
                    payload["refresh_cached"] = True
                    return payload

        payload = build_inventory_snapshot(self.skills_root, self.candidate_root)
        reconcile_cases(payload)
        payload["refresh_cached"] = False
        append_audit_event(
            AuditEvent(
                event_type="inventory_refresh",
                subject="skills",
                detail="refreshed local skill and source inventory",
                host_id=self.host_id,
                evidence_codes=[item["severity"] for item in payload.get("incidents", [])[:6]],
            )
        )
        with self._inventory_refresh_lock:
            self._inventory_refresh_cache["payload"] = payload
            self._inventory_refresh_cache["expires_at"] = now + max(
                10.0,
                load_poll_profile().get("passive_inventory_ms", 120000) / 1000.0,
            )
        return payload

    def public_readiness(self) -> dict[str, object]:
        payload = run_public_readiness_scan(REPO_ROOT)
        append_audit_event(
            AuditEvent(
                event_type="public_readiness_run",
                subject="repo",
                detail="evaluated public release readiness",
                host_id=self.host_id,
                evidence_codes=[item["code"] for item in payload.get("findings", [])[:6]],
            )
        )
        return payload

    def evaluate_skill(self, body: dict[str, object]) -> dict[str, object]:
        skill_name = str(body.get("skill_name") or "").strip()
        domain = str(body.get("domain") or "auto").strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        candidates = [self.candidate_root / skill_name, self.skills_root / skill_name]
        target = None
        if domain == "candidate":
            target = self.candidate_root / skill_name
        elif domain == "installed":
            target = self.skills_root / skill_name
        else:
            for item in candidates:
                if item.is_dir():
                    target = item
                    break
        if target is None or not target.is_dir():
            raise FileNotFoundError(f"skill not found: {skill_name}")
        source_root = self.candidate_root if target.is_relative_to(self.candidate_root) else self.skills_root
        summary = summarize_findings(scan_skill_dir_content(target))["findings"] + summarize_findings(scan_skill_tree(target, source_root))["findings"]
        codes = list(dict.fromkeys(row["code"] for row in summary))
        severity = "low"
        if any(row["severity"] == "critical" for row in summary):
            severity = "critical"
        elif any(row["severity"] == "high" for row in summary):
            severity = "high"
        decision = PolicyDecision(
            subject=skill_name,
            action="quarantine" if severity in {"critical", "high"} else "keep",
            reason=f"evaluated {len(summary)} findings for skill",
            severity=severity,
            requires_confirmation=severity in {"critical", "high"},
            host_id=self.host_id,
            evidence_codes=codes,
        )
        append_audit_event(
            AuditEvent(
                event_type="admission_evaluate",
                subject=skill_name,
                detail=f"evaluated skill in {domain} domain",
                host_id=self.host_id,
                requires_confirmation=decision.requires_confirmation,
                evidence_codes=codes,
            )
        )
        return {"decision": decision.to_dict(), "findings": summary}


_LOOPBACK_ORIGIN_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _requested_origin(handler: BaseHTTPRequestHandler) -> str:
    return str(handler.headers.get("Origin", "")).strip()


def _resolve_allowed_origin(origin: str) -> str:
    requested = str(origin or "").strip()
    if not requested:
        return ""
    if requested == "null":
        return "null"
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
    if not allowed_origin:
        allowed_origin = "*"
    handler.send_header("Access-Control-Allow-Origin", allowed_origin)
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Private-Network", "true")
    handler.send_header("Vary", "Origin")


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
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
            if self.path == "/v1/health":
                _json_response(self, HTTPStatus.OK, state.health())
                return
            if self.path == "/v1/about":
                _json_response(self, HTTPStatus.OK, about_payload(state.host_id))
                return
            if self.path == "/v1/privacy/status":
                checks = state.load_self_checks() or state.run_self_checks()
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "host_id": state.host_id,
                        "privacy_passed": checks.get("privacy_passed", False),
                        "privacy_findings": checks.get("privacy_findings", []),
                    },
                )
                return
            if self.path == "/v1/inventory/skills":
                inventory = load_cached_inventory()
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "skills": inventory.get("skills", [])})
                return
            if self.path == "/v1/inventory/sources":
                inventory = load_cached_inventory()
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "sources": inventory.get("sources", [])})
                return
            if self.path == "/v1/incidents":
                inventory = load_cached_inventory()
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "incidents": inventory.get("incidents", [])})
                return
            if self.path == "/v1/audit-log":
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "events": read_audit_events()})
                return
            if self.path == "/v1/skill-game/status":
                inventory = load_cached_inventory()
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, **skill_game_status_payload(inventory)})
                return
            if self.path == "/v1/collaboration/status":
                inventory = load_cached_inventory()
                payload = collaboration_status_payload(inventory)
                payload["stack_runtime"] = stack_runtime_snapshot(fallback_events=payload.get("recent_events", []))
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, **payload})
                return
            if self.path == "/v1/agent-runtime/status":
                inventory = load_cached_inventory()
                payload = stack_runtime_snapshot(force_refresh=True)
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "host_id": state.host_id,
                        "skill_count": int(inventory.get("skill_count") or 0),
                        "incident_count": int(inventory.get("incident_count") or 0),
                        "advisor_note": str(inventory.get("advisor_note") or ""),
                        "stack_runtime": payload,
                    },
                )
                return
            if self.path == "/v1/mitigation/cases":
                _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "cases": list_cases()})
                return
            if self.path == "/v1/public-readiness":
                _json_response(self, HTTPStatus.OK, load_cached_public_readiness())
                return
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not_found"})

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
                if self.path == "/v1/self-checks/run":
                    _json_response(self, HTTPStatus.OK, state.run_self_checks())
                    return
                if self.path == "/v1/inventory/refresh":
                    _json_response(self, HTTPStatus.OK, state.inventory_refresh(force=True))
                    return
                if self.path == "/v1/public-readiness/run":
                    _json_response(self, HTTPStatus.OK, state.public_readiness())
                    return
                if self.path == "/v1/skill-game/record":
                    inventory = load_cached_inventory()
                    task = str(payload.get("task") or "").strip()
                    if not task:
                        raise ValueError("task is required")
                    required_skills = [str(item).strip() for item in (payload.get("required_skills") or []) if str(item).strip()]
                    used_skills = [str(item).strip() for item in (payload.get("used_skills") or []) if str(item).strip()]
                    enforcer_pass = payload.get("enforcer_pass")
                    if enforcer_pass not in {None, True, False}:
                        raise ValueError("enforcer_pass must be true, false, or null")
                    result = record_skill_game_payload(
                        inventory=inventory,
                        task=task,
                        required_skills=required_skills,
                        used_skills=used_skills,
                        arbiter_report=str(payload.get("arbiter_report") or ""),
                        audit_report=str(payload.get("audit_report") or ""),
                        enforcer_pass=enforcer_pass,
                        dry_run=bool(payload.get("dry_run")),
                    )
                    append_audit_event(
                        AuditEvent(
                            event_type="skill_game_record",
                            subject=task,
                            detail=f"recorded skill-game event clear_run={str(result.get('clear_run', False)).lower()}",
                            host_id=state.host_id,
                            evidence_codes=[str(item.get("category") or "") for item in result.get("breakdown", [])[:6]],
                        )
                    )
                    _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, **result})
                    return
                if self.path == "/v1/collaboration/record":
                    inventory = load_cached_inventory()
                    task = str(payload.get("task") or "").strip()
                    outcome = str(payload.get("outcome") or "success").strip()
                    if not task:
                        raise ValueError("task is required")
                    result = record_collaboration_payload(
                        inventory=inventory,
                        host_id=state.host_id,
                        task=task,
                        outcome=outcome,
                        collaborators=[str(item).strip() for item in (payload.get("collaborators") or []) if str(item).strip()],
                        repo_scope=[str(item).strip() for item in (payload.get("repo_scope") or []) if str(item).strip()],
                        skills_used=[str(item).strip() for item in (payload.get("skills_used") or []) if str(item).strip()],
                        proposed_skill_work=[item for item in (payload.get("proposed_skill_work") or []) if isinstance(item, dict)],
                        note=str(payload.get("note") or ""),
                        stability=str(payload.get("stability") or "emerging"),
                        dry_run=bool(payload.get("dry_run")),
                    )
                    append_audit_event(
                        AuditEvent(
                            event_type="collaboration_record",
                            subject=task,
                            detail=f"recorded collaboration outcome={outcome}",
                            host_id=state.host_id,
                            evidence_codes=[str(item.get("action") or "") for item in result.get("recommended_skill_work", [])[:6]],
                        )
                    )
                    _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, **result})
                    return
                if self.path == "/v1/mitigation/plan":
                    subject = str(payload.get("subject") or "").strip()
                    if not subject:
                        raise ValueError("subject is required")
                    _json_response(self, HTTPStatus.OK, {"host_id": state.host_id, "case": plan_case(subject)})
                    return
                if self.path == "/v1/mitigation/execute":
                    case_id = str(payload.get("case_id") or "").strip()
                    action = str(payload.get("action") or "").strip()
                    if not case_id or not action:
                        raise ValueError("case_id and action are required")
                    _json_response(
                        self,
                        HTTPStatus.OK,
                        {
                            "host_id": state.host_id,
                            **execute_case_action(case_id, action, skills_root=state.skills_root, candidate_root=state.candidate_root),
                        },
                    )
                    return
                if self.path == "/v1/admission/evaluate":
                    _json_response(self, HTTPStatus.OK, state.evaluate_skill(payload))
                    return
                if self.path == "/v1/quarantine/apply":
                    skill_name = str(payload.get("skill_name") or "").strip()
                    if not skill_name:
                        raise ValueError("skill_name is required")
                    decision = apply_quarantine(skill_name, state.skills_root)
                    incident = IncidentRecord(
                        incident_id=f"quarantine-{skill_name}",
                        category="quarantine",
                        severity="high",
                        subject=skill_name,
                        summary="skill quarantined and blacklisted",
                        host_id=state.host_id,
                        requires_confirmation=False,
                        evidence_codes=decision.evidence_codes,
                    )
                    _json_response(self, HTTPStatus.OK, {"decision": decision.to_dict(), "incident": incident.to_dict()})
                    return
                if self.path == "/v1/quarantine/release":
                    skill_name = str(payload.get("skill_name") or "").strip()
                    if not skill_name:
                        raise ValueError("skill_name is required")
                    _json_response(self, HTTPStatus.OK, {"decision": release_quarantine(skill_name, state.skills_root).to_dict()})
                    return
                if self.path == "/v1/review/accept":
                    subject = str(payload.get("subject") or "").strip()
                    if not subject:
                        raise ValueError("subject is required")
                    inventory = load_cached_inventory()
                    row = next((item for item in inventory.get("skills", []) if item.get("name") == subject), None)
                    if row is None:
                        raise FileNotFoundError(f"skill not found in inventory: {subject}")
                    decision = accept_subject(
                        subject,
                        review_fingerprint=str(row.get("review_fingerprint") or "").strip(),
                        ownership=str(row.get("ownership") or ""),
                        legitimacy_status=str(row.get("legitimacy_status") or ""),
                        reason=str(row.get("legitimacy_reason") or "accepted reviewed subject on local host"),
                    )
                    _json_response(self, HTTPStatus.OK, {"decision": decision.to_dict()})
                    return
                if self.path == "/v1/review/revoke":
                    subject = str(payload.get("subject") or "").strip()
                    if not subject:
                        raise ValueError("subject is required")
                    _json_response(self, HTTPStatus.OK, {"decision": revoke_subject(subject).to_dict()})
                    return
                if self.path == "/v1/actions/confirm":
                    action = str(payload.get("action") or "").strip()
                    if action == "delete_skill":
                        skill_name = str(payload.get("skill_name") or "").strip()
                        _json_response(self, HTTPStatus.OK, {"decision": confirm_delete_skill(skill_name, state.skills_root).to_dict()})
                        return
                    if action == "kill_process":
                        pid = int(payload.get("pid") or 0)
                        _json_response(self, HTTPStatus.OK, {"decision": confirm_kill_process(pid).to_dict()})
                        return
                    raise ValueError(f"unsupported action: {action}")
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not_found"})
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
