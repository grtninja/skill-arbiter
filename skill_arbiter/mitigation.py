from __future__ import annotations

import json
import shutil
from pathlib import Path

from .audit_log import append_audit_event
from .contracts import AuditEvent, MitigationCase, MitigationStep, PolicyDecision, utc_now
from .inventory import build_inventory_snapshot, load_cached_inventory
from .paths import DEFAULT_CANDIDATES_ROOT, DEFAULT_SKILLS_ROOT, host_id, mitigation_cases_root, quarantine_artifacts_root
from .quarantine import apply_quarantine, confirm_delete_skill
from .threat_catalog import ALWAYS_BLOCK_CODES, describe_codes


STRIP_CODES = {
    "vendored_python_binary",
    "hidden_python_script",
    "backup_python_script",
    "editor_swap_python_script",
    "untracked_python_script",
}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "monitor": 3, "trusted": 4, "low": 5}


def _case_path(case_id: str) -> Path:
    return mitigation_cases_root() / f"{case_id}.json"


def _load_case(case_id: str) -> dict[str, object]:
    path = _case_path(case_id)
    if not path.is_file():
        raise FileNotFoundError(f"mitigation case not found: {case_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_case(payload: dict[str, object]) -> None:
    path = _case_path(str(payload["case_id"]))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _inventory_subject(subject: str, inventory: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    skills = inventory.get("skills", [])
    incidents = inventory.get("incidents", [])
    row = next((item for item in skills if item.get("name") == subject), None)
    if row is None:
        raise FileNotFoundError(f"skill not found in inventory: {subject}")
    incident_rows = [item for item in incidents if item.get("subject") == subject]
    return row, incident_rows


def _case_id(subject: str) -> str:
    return f"mitigation-{subject.replace('/', '-').replace(' ', '-').lower()}"


def _step(
    step_id: str,
    label: str,
    summary: str,
    *,
    status: str = "pending",
    requires_confirmation: bool = False,
    auto_allowed: bool = False,
) -> MitigationStep:
    return MitigationStep(
        step_id=step_id,
        label=label,
        status=status,
        summary=summary,
        requires_confirmation=requires_confirmation,
        auto_allowed=auto_allowed,
    )


def _classification(row: dict[str, object], codes: list[str], incident_rows: list[dict[str, object]]) -> tuple[str, bool, bool, str]:
    severity = str(row.get("risk_class") or "low")
    if any(str(item.get("severity") or "") == "critical" for item in incident_rows):
        severity = "critical"
    elif any(str(item.get("severity") or "") == "high" for item in incident_rows):
        severity = "high"
    legitimacy_status = str(row.get("legitimacy_status") or "")
    hostile = legitimacy_status == "blocked_hostile" or any(code in ALWAYS_BLOCK_CODES for code in codes)
    rebuildable = str(row.get("origin") or "") in {
        "overlay_candidate_installed",
        "skill_candidates",
        "openai_builtin",
        "openai_builtin_system",
    }
    if hostile:
        classification = "hostile"
    elif legitimacy_status in {"official_sensitive", "owned_sensitive", "official_review", "owned_review", "manual_review"}:
        classification = "manual_review"
    elif rebuildable:
        classification = "legit_rebuildable"
    else:
        classification = "manual_review"
    return classification, hostile, rebuildable, severity


def _recommended_path(classification: str, hostile: bool, rebuildable: bool) -> tuple[str, str, list[str]]:
    if hostile:
        return (
            "contain_blacklist_remove",
            "Hostile path: contain immediately, blacklist, remove/refactor, then audit adjacent vectors.",
            ["quarantine", "blacklist", "remove_or_refactor", "audit_vectors", "audit_sources", "repeat"],
        )
    if rebuildable:
        return (
            "contain_request_rebuild",
            "Owned or rebuildable path: quarantine, request review, then rebuild from a trusted local source.",
            ["quarantine", "strip", "request", "rebuild", "audit_vectors", "repeat"],
        )
    if classification == "manual_review":
        return (
            "contain_review_refactor",
            "Manual-review path: quarantine, request review, then refactor or remove once provenance is resolved.",
            ["quarantine", "request", "audit_vectors", "audit_sources", "remove_or_refactor", "repeat"],
        )
    return (
        "contain_review",
        "Default containment path: quarantine, review, document, and rescan.",
        ["quarantine", "audit_vectors", "document", "repeat"],
    )


def _plan_steps(hostile: bool, rebuildable: bool) -> list[MitigationStep]:
    steps = [
        _step("preserve_evidence", "Preserve Evidence", "Cache the case and retain local evidence before mutation.", status="done", auto_allowed=True),
        _step("quarantine", "Quarantine", "Blacklist and quarantine the subject immediately to stop reuse.", auto_allowed=True),
        _step("strip", "Strip", "Move suspicious runtime artifacts and stray Python out of the live skill surface.", requires_confirmation=True),
        _step("report", "Report", "Write a case report with findings, provenance, and operator-facing summary.", auto_allowed=True),
        _step("request", "Request Review", "Request owner review for skills that may be legitimate or locally maintained.", auto_allowed=True),
        _step("rebuild", "Rebuild Clean", "Rebuild from a trusted local candidate or known-good baseline.", requires_confirmation=True),
        _step("blacklist", "Blacklist Hostile", "Mark the subject hostile and keep it denied on the host.", auto_allowed=True),
        _step("remove_or_refactor", "Remove or Refactor", "Delete hostile installed skills or refactor local candidates to a safe shape.", requires_confirmation=True),
        _step("audit_vectors", "Audit Threat Vectors", "Review the exact execution, persistence, and credential vectors that triggered the case.", auto_allowed=True),
        _step("audit_sources", "Audit Sources", "Review catalog and source provenance for the subject and similar imports.", auto_allowed=True),
        _step("adjacent_vectors", "Evaluate Adjacent Vectors", "Check adjacent skills, scripts, and hosts for the same indicators.", auto_allowed=True),
        _step("document", "Document and Report", "Persist the mitigation outcome and operator notes to the local case file.", auto_allowed=True),
        _step("repeat", "Repeat Scan", "Refresh inventory and rescore after containment or rebuild.", auto_allowed=True),
    ]
    for step in steps:
        if hostile and step.step_id in {"request", "rebuild"}:
            step.status = "skipped"
            step.summary = "Skipped because the subject is classified as hostile."
        if (not hostile) and step.step_id == "blacklist":
            step.status = "skipped"
            step.summary = "Skipped unless the subject is reclassified as hostile."
        if (not rebuildable) and step.step_id == "rebuild":
            step.status = "skipped"
            step.summary = "Skipped because there is no trusted rebuild path."
    return steps


def _case_report_payload(case_payload: dict[str, object]) -> str:
    lines = [
        f"# Mitigation Case: {case_payload['subject']}",
        "",
        f"- Case ID: `{case_payload['case_id']}`",
        f"- Classification: `{case_payload['classification']}`",
        f"- Severity: `{case_payload['severity']}`",
        f"- Source domain: `{case_payload['source_domain']}`",
        f"- Hostile: `{case_payload['hostile']}`",
        f"- Rebuildable: `{case_payload['rebuildable']}`",
        "",
        "## Findings",
        "",
        ", ".join(f"`{code}`" for code in case_payload.get("finding_codes", [])) or "_No finding codes._",
        "",
        "## Steps",
        "",
    ]
    for step in case_payload.get("steps", []):
        lines.append(
            f"- `{step['step_id']}`: `{step['status']}` | {step['label']} | {step['summary']}"
        )
    lines.append("")
    return "\n".join(lines)


def _mark_step(case_payload: dict[str, object], step_id: str, status: str, summary: str | None = None) -> None:
    for step in case_payload.get("steps", []):
        if step.get("step_id") == step_id:
            step["status"] = status
            if summary:
                step["summary"] = summary


def plan_case(subject: str, inventory: dict[str, object] | None = None) -> dict[str, object]:
    payload = inventory or load_cached_inventory()
    row, incident_rows = _inventory_subject(subject, payload)
    finding_codes = list(dict.fromkeys(list(row.get("finding_codes", [])) + [code for item in incident_rows for code in item.get("evidence_codes", [])]))
    classification, hostile, rebuildable, severity = _classification(row, finding_codes, incident_rows)
    recommended_path, operator_summary, next_actions = _recommended_path(classification, hostile, rebuildable)
    case = MitigationCase(
        case_id=_case_id(subject),
        subject=subject,
        classification=classification,
        severity=severity,
        source_domain=str(row.get("source_type") or "unknown"),
        hostile=hostile,
        rebuildable=rebuildable,
        summary=(
            "Hostile indicators detected. Quarantine first, then blacklist and remove from the live surface."
            if hostile
            else "Likely legitimate but risky. Quarantine, strip unsafe artifacts, then rebuild from a trusted source."
            if rebuildable
            else "Needs manual review. Quarantine first, then request review and refactor or remove."
        ),
        operator_summary=operator_summary,
        recommended_path=recommended_path,
        finding_codes=finding_codes,
        evidence_codes=list(dict.fromkeys(finding_codes[:12])),
        finding_details=describe_codes(finding_codes),
        next_actions=next_actions,
        steps=_plan_steps(hostile, rebuildable),
    )
    result = case.to_dict()
    _save_case(result)
    append_audit_event(
        AuditEvent(
            event_type="mitigation_plan",
            subject=subject,
            detail=f"planned mitigation case '{case.classification}'",
            host_id=host_id(),
            evidence_codes=case.evidence_codes[:6],
        )
    )
    return result


def list_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(mitigation_cases_root().glob("*.json"), reverse=True):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    rows.sort(key=lambda item: (SEVERITY_ORDER.get(str(item.get("severity") or ""), 9), str(item.get("updated_at") or "")))
    return rows


def reconcile_cases(inventory: dict[str, object] | None = None) -> list[dict[str, object]]:
    payload = inventory or load_cached_inventory()
    incident_subjects = {str(item.get("subject") or "") for item in payload.get("incidents", [])}
    refreshed: list[dict[str, object]] = []
    for path in sorted(mitigation_cases_root().glob("*.json")):
        try:
            case_payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        subject = str(case_payload.get("subject") or "").strip()
        if not subject:
            continue
        if subject not in incident_subjects:
            path.unlink(missing_ok=True)
            append_audit_event(
                AuditEvent(
                    event_type="mitigation_case_resolved",
                    subject=subject,
                    detail="removed stale mitigation case after inventory refresh",
                    host_id=host_id(),
                    evidence_codes=[],
                )
            )
            continue
        refreshed.append(plan_case(subject, payload))
    return refreshed


def _target_skill_dir(case_payload: dict[str, object], skills_root: Path, candidate_root: Path) -> Path | None:
    subject = str(case_payload["subject"])
    for candidate in (skills_root / subject, candidate_root / subject):
        if candidate.is_dir():
            return candidate
    return None


def _strip_suspicious_files(target: Path, subject: str) -> list[str]:
    moved: list[str] = []
    destination_root = quarantine_artifacts_root() / subject
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(target).as_posix()
        lower = rel.lower()
        is_stale_python = lower.endswith(".py") and (
            lower.split("/")[-1].startswith(".")
            or any(token in lower for token in ("backup", ".bak", ".tmp", ".old", ".copy", "~"))
        )
        is_python_binary = lower.endswith("/python.exe") or lower.endswith("/pythonw.exe") or lower in {"python.exe", "pythonw.exe"}
        if not is_stale_python and not is_python_binary:
            continue
        destination = destination_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        moved.append(rel)
    return moved


def execute_case_action(
    case_id: str,
    action: str,
    *,
    skills_root: Path | None = None,
    candidate_root: Path | None = None,
) -> dict[str, object]:
    case_payload = _load_case(case_id)
    current_host = host_id()
    installed_root = skills_root or DEFAULT_SKILLS_ROOT
    overlay_root = candidate_root or DEFAULT_CANDIDATES_ROOT
    subject = str(case_payload["subject"])
    outcome: dict[str, object]

    if action in {"quarantine", "blacklist"}:
        decision = apply_quarantine(subject, installed_root)
        _mark_step(case_payload, "quarantine", "done")
        if action == "blacklist":
            _mark_step(case_payload, "blacklist", "done")
        outcome = {"decision": decision.to_dict()}
    elif action == "strip":
        target = _target_skill_dir(case_payload, installed_root, overlay_root)
        if target is None:
            moved = []
        else:
            moved = _strip_suspicious_files(target, subject)
        summary = "No strip candidates found." if not moved else f"Moved {len(moved)} suspicious artifacts into quarantine storage."
        _mark_step(case_payload, "strip", "done", summary)
        append_audit_event(
            AuditEvent(
                event_type="mitigation_strip",
                subject=subject,
                detail=summary,
                host_id=current_host,
                evidence_codes=case_payload.get("evidence_codes", [])[:6],
            )
        )
        outcome = {"moved": moved}
    elif action == "request":
        _mark_step(case_payload, "request", "done", "Owner review requested in local case history.")
        append_audit_event(
            AuditEvent(
                event_type="mitigation_request_review",
                subject=subject,
                detail="recorded request for owner review",
                host_id=current_host,
                evidence_codes=case_payload.get("evidence_codes", [])[:6],
            )
        )
        outcome = {"requested": True}
    elif action == "rebuild":
        source = overlay_root / subject
        target = installed_root / subject
        if not source.is_dir():
            raise FileNotFoundError(f"no trusted rebuild source found for {subject}")
        if target.is_dir():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        _mark_step(case_payload, "rebuild", "done", "Rebuilt installed skill from trusted local candidate.")
        append_audit_event(
            AuditEvent(
                event_type="mitigation_rebuild",
                subject=subject,
                detail="rebuilt installed skill from trusted local candidate",
                host_id=current_host,
                evidence_codes=case_payload.get("evidence_codes", [])[:6],
            )
        )
        outcome = {"rebuilt_from": str(source)}
    elif action == "remove_or_refactor":
        target = installed_root / subject
        if target.is_dir():
            decision = confirm_delete_skill(subject, installed_root)
            _mark_step(case_payload, "remove_or_refactor", "done", "Removed installed hostile or superseded skill.")
            outcome = {"decision": decision.to_dict()}
        else:
            _mark_step(case_payload, "remove_or_refactor", "done", "Candidate requires manual repository refactor; no installed skill deleted.")
            outcome = {"decision": PolicyDecision(
                subject=subject,
                action="refactor_candidate",
                reason="candidate exists in repo only; manual refactor required",
                severity=str(case_payload.get("severity") or "high"),
                requires_confirmation=False,
                host_id=current_host,
                evidence_codes=case_payload.get("evidence_codes", [])[:6],
            ).to_dict()}
    elif action in {"audit_vectors", "audit_sources", "adjacent_vectors", "document"}:
        label_map = {
            "audit_vectors": "vector audit recorded",
            "audit_sources": "source audit recorded",
            "adjacent_vectors": "adjacent vector audit recorded",
            "document": "case documented in local report",
        }
        _mark_step(case_payload, action, "done", label_map[action])
        if action == "document":
            report_path = mitigation_cases_root() / f"{case_id}.md"
            report_path.write_text(_case_report_payload(case_payload), encoding="utf-8")
            outcome = {"report_path": str(report_path)}
        else:
            outcome = {"recorded": True}
        append_audit_event(
            AuditEvent(
                event_type=f"mitigation_{action}",
                subject=subject,
                detail=label_map[action],
                host_id=current_host,
                evidence_codes=case_payload.get("evidence_codes", [])[:6],
            )
        )
    elif action == "repeat":
        inventory = build_inventory_snapshot(installed_root, overlay_root)
        refreshed = plan_case(subject, inventory)
        _mark_step(refreshed, "repeat", "done", "Re-ran inventory and refreshed mitigation plan.")
        _save_case(refreshed)
        outcome = {"inventory": {"skill_count": inventory["skill_count"], "incident_count": inventory["incident_count"]}}
        return {"case": refreshed, "outcome": outcome}
    else:
        raise ValueError(f"unsupported mitigation action: {action}")

    _mark_step(case_payload, "report", "done", "Case activity logged for operator review.")
    _mark_step(case_payload, "document", "done", "Case state updated in local storage.")
    case_payload["updated_at"] = utc_now()
    _save_case(case_payload)
    return {"case": case_payload, "outcome": outcome}
