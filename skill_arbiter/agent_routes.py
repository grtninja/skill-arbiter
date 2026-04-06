from __future__ import annotations

from http import HTTPStatus
from types import ModuleType


def handle_get(module: ModuleType, state, path: str) -> tuple[HTTPStatus, dict]:
    if path == "/v1/health":
        return HTTPStatus.OK, state.health()
    if path == "/v1/ready":
        return HTTPStatus.OK, state.ready()
    if path == "/v1/about":
        return HTTPStatus.OK, module.about_payload(state.host_id)
    if path == "/v1/privacy/status":
        checks = state.load_self_checks() or state.run_self_checks()
        return HTTPStatus.OK, {
            "host_id": state.host_id,
            "privacy_passed": checks.get("privacy_passed", False),
            "privacy_findings": checks.get("privacy_findings", []),
        }
    if path == "/v1/inventory/skills":
        inventory = module.load_cached_inventory()
        return HTTPStatus.OK, {"host_id": state.host_id, "skills": inventory.get("skills", [])}
    if path == "/v1/inventory/sources":
        inventory = module.load_cached_inventory()
        return HTTPStatus.OK, {"host_id": state.host_id, "sources": inventory.get("sources", [])}
    if path == "/v1/incidents":
        inventory = module.load_cached_inventory()
        return HTTPStatus.OK, {"host_id": state.host_id, "incidents": inventory.get("incidents", [])}
    if path == "/v1/audit-log":
        return HTTPStatus.OK, {"host_id": state.host_id, "events": module.read_audit_events()}
    if path == "/v1/skill-game/status":
        inventory = module.load_cached_inventory()
        return HTTPStatus.OK, {"host_id": state.host_id, **module.skill_game_status_payload(inventory)}
    if path == "/v1/quests/status":
        inventory = module.load_cached_inventory()
        return HTTPStatus.OK, {"host_id": state.host_id, **module.quest_status_payload(inventory)}
    if path == "/v1/collaboration/status":
        inventory = module.load_cached_inventory()
        payload = module.collaboration_status_payload(inventory)
        payload["stack_runtime"] = module.stack_runtime_snapshot(fallback_events=payload.get("recent_events", []))
        return HTTPStatus.OK, {"host_id": state.host_id, **payload}
    if path == "/v1/agent-runtime/status":
        inventory = module.load_cached_inventory()
        payload = module.stack_runtime_snapshot(force_refresh=True, refresh_local_supervision=True)
        return HTTPStatus.OK, {
            "host_id": state.host_id,
            "skill_count": int(inventory.get("skill_count") or 0),
            "incident_count": int(inventory.get("incident_count") or 0),
            "advisor_note": str(inventory.get("advisor_note") or ""),
            "stack_runtime": payload,
        }
    if path == "/v1/mitigation/cases":
        return HTTPStatus.OK, {"host_id": state.host_id, "cases": module.list_cases()}
    if path == "/v1/public-readiness":
        return HTTPStatus.OK, module.load_cached_public_readiness()
    return HTTPStatus.NOT_FOUND, {"error": "not_found"}


def handle_post(module: ModuleType, state, path: str, payload: dict[str, object]) -> tuple[HTTPStatus, dict]:
    if path == "/v1/self-checks/run":
        return HTTPStatus.OK, state.run_self_checks()
    if path == "/v1/inventory/refresh":
        return HTTPStatus.OK, state.inventory_refresh(force=True)
    if path == "/v1/public-readiness/run":
        return HTTPStatus.OK, state.public_readiness()
    if path == "/v1/skill-game/record":
        inventory = module.load_cached_inventory()
        task = str(payload.get("task") or "").strip()
        if not task:
            raise ValueError("task is required")
        required_skills = [str(item).strip() for item in (payload.get("required_skills") or []) if str(item).strip()]
        used_skills = [str(item).strip() for item in (payload.get("used_skills") or []) if str(item).strip()]
        enforcer_pass = payload.get("enforcer_pass")
        if enforcer_pass not in {None, True, False}:
            raise ValueError("enforcer_pass must be true, false, or null")
        result = module.record_skill_game_payload(
            inventory=inventory,
            task=task,
            required_skills=required_skills,
            used_skills=used_skills,
            arbiter_report=str(payload.get("arbiter_report") or ""),
            audit_report=str(payload.get("audit_report") or ""),
            enforcer_pass=enforcer_pass,
            dry_run=bool(payload.get("dry_run")),
        )
        module.append_audit_event(
            module.AuditEvent(
                event_type="skill_game_record",
                subject=task,
                detail=f"recorded skill-game event clear_run={str(result.get('clear_run', False)).lower()}",
                host_id=state.host_id,
                evidence_codes=[str(item.get("category") or "") for item in result.get("breakdown", [])[:6]],
            )
        )
        return HTTPStatus.OK, {"host_id": state.host_id, **result}
    if path == "/v1/quests/record":
        inventory = module.load_cached_inventory()
        request_text = str(payload.get("request") or "").strip()
        outcome = str(payload.get("outcome") or "success").strip().lower()
        if not request_text:
            raise ValueError("request is required")
        result = module.record_quest_payload(
            inventory=inventory,
            host_id=state.host_id,
            request=request_text,
            outcome=outcome,
            skills_used=[str(item).strip() for item in (payload.get("skills_used") or []) if str(item).strip()],
            required_skills=[str(item).strip() for item in (payload.get("required_skills") or []) if str(item).strip()],
            repo_scope=[str(item).strip() for item in (payload.get("repo_scope") or []) if str(item).strip()],
            checkpoints=[item for item in (payload.get("checkpoints") or []) if isinstance(item, dict)],
            steps=[item for item in (payload.get("steps") or []) if isinstance(item, dict)],
            quest_id=str(payload.get("quest_id") or ""),
            chain_id=str(payload.get("chain_id") or ""),
            title=str(payload.get("title") or ""),
            final_outcome=str(payload.get("final_outcome") or ""),
            deliverables=[str(item).strip() for item in (payload.get("deliverables") or []) if str(item).strip()],
            evidence=[str(item).strip() for item in (payload.get("evidence") or []) if str(item).strip()],
            meta_harness=bool(payload.get("meta_harness")),
            enforcer_pass=payload.get("enforcer_pass") if payload.get("enforcer_pass") in {None, True, False} else None,
            dry_run=bool(payload.get("dry_run")),
        )
        module.append_audit_event(
            module.AuditEvent(
                event_type="quest_record",
                subject=str(result.get("quest", {}).get("quest_id") or request_text),
                detail=f"recorded quest outcome={outcome}",
                host_id=state.host_id,
                evidence_codes=[str(item.get("skill") or "") for item in result.get("quest", {}).get("skill_xp_awards", [])[:6]],
            )
        )
        return HTTPStatus.OK, {"host_id": state.host_id, **result}
    if path == "/v1/collaboration/record":
        inventory = module.load_cached_inventory()
        task = str(payload.get("task") or "").strip()
        outcome = str(payload.get("outcome") or "success").strip()
        if not task:
            raise ValueError("task is required")
        result = module.record_collaboration_payload(
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
        module.append_audit_event(
            module.AuditEvent(
                event_type="collaboration_record",
                subject=task,
                detail=f"recorded collaboration outcome={outcome}",
                host_id=state.host_id,
                evidence_codes=[str(item.get("action") or "") for item in result.get("recommended_skill_work", [])[:6]],
            )
        )
        return HTTPStatus.OK, {"host_id": state.host_id, **result}
    if path == "/v1/mitigation/plan":
        subject = str(payload.get("subject") or "").strip()
        if not subject:
            raise ValueError("subject is required")
        return HTTPStatus.OK, {"host_id": state.host_id, "case": module.plan_case(subject)}
    if path == "/v1/mitigation/execute":
        case_id = str(payload.get("case_id") or "").strip()
        action = str(payload.get("action") or "").strip()
        if not case_id or not action:
            raise ValueError("case_id and action are required")
        return HTTPStatus.OK, {
            "host_id": state.host_id,
            **module.execute_case_action(case_id, action, skills_root=state.skills_root, candidate_root=state.candidate_root),
        }
    if path == "/v1/admission/evaluate":
        return HTTPStatus.OK, state.evaluate_skill(payload)
    if path == "/v1/quarantine/apply":
        skill_name = str(payload.get("skill_name") or "").strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        decision = module.apply_quarantine(skill_name, state.skills_root)
        incident = module.IncidentRecord(
            incident_id=f"quarantine-{skill_name}",
            category="quarantine",
            severity="high",
            subject=skill_name,
            summary="skill quarantined and blacklisted",
            host_id=state.host_id,
            requires_confirmation=False,
            evidence_codes=decision.evidence_codes,
        )
        return HTTPStatus.OK, {"decision": decision.to_dict(), "incident": incident.to_dict()}
    if path == "/v1/quarantine/release":
        skill_name = str(payload.get("skill_name") or "").strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        return HTTPStatus.OK, {"decision": module.release_quarantine(skill_name, state.skills_root).to_dict()}
    if path == "/v1/review/accept":
        subject = str(payload.get("subject") or "").strip()
        if not subject:
            raise ValueError("subject is required")
        inventory = module.load_cached_inventory()
        row = next((item for item in inventory.get("skills", []) if item.get("name") == subject), None)
        if row is None:
            raise FileNotFoundError(f"skill not found in inventory: {subject}")
        decision = module.accept_subject(
            subject,
            review_fingerprint=str(row.get("review_fingerprint") or "").strip(),
            ownership=str(row.get("ownership") or ""),
            legitimacy_status=str(row.get("legitimacy_status") or ""),
            reason=str(row.get("legitimacy_reason") or "accepted reviewed subject on local host"),
        )
        return HTTPStatus.OK, {"decision": decision.to_dict()}
    if path == "/v1/review/revoke":
        subject = str(payload.get("subject") or "").strip()
        if not subject:
            raise ValueError("subject is required")
        return HTTPStatus.OK, {"decision": module.revoke_subject(subject).to_dict()}
    if path == "/v1/actions/confirm":
        action = str(payload.get("action") or "").strip()
        if action == "delete_skill":
            skill_name = str(payload.get("skill_name") or "").strip()
            return HTTPStatus.OK, {"decision": module.confirm_delete_skill(skill_name, state.skills_root).to_dict()}
        if action == "kill_process":
            pid = int(payload.get("pid") or 0)
            return HTTPStatus.OK, {"decision": module.confirm_kill_process(pid).to_dict()}
        raise ValueError(f"unsupported action: {action}")
    return HTTPStatus.NOT_FOUND, {"error": "not_found"}
