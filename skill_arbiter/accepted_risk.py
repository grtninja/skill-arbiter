from __future__ import annotations

import json

from .audit_log import append_audit_event
from .contracts import AuditEvent, PolicyDecision
from .paths import accepted_risk_path, host_id


def load_acceptance_state() -> dict[str, object]:
    path = accepted_risk_path()
    if not path.is_file():
        return {"accepted_subjects": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"accepted_subjects": {}}
    if not isinstance(payload, dict):
        return {"accepted_subjects": {}}
    subjects = payload.get("accepted_subjects")
    if not isinstance(subjects, dict):
        payload["accepted_subjects"] = {}
    return payload


def _save_acceptance_state(payload: dict[str, object]) -> None:
    accepted_risk_path().write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def accepted_subject_entry(subject: str) -> dict[str, object] | None:
    payload = load_acceptance_state()
    accepted = payload.get("accepted_subjects", {})
    if not isinstance(accepted, dict):
        return None
    row = accepted.get(subject)
    return row if isinstance(row, dict) else None


def subject_is_accepted(subject: str, review_fingerprint: str) -> bool:
    entry = accepted_subject_entry(subject)
    if not entry:
        return False
    stored_fingerprint = str(entry.get("review_fingerprint") or "").strip()
    return bool(stored_fingerprint) and stored_fingerprint == str(review_fingerprint or "").strip()


def accept_subject(
    subject: str,
    *,
    review_fingerprint: str,
    ownership: str,
    legitimacy_status: str,
    reason: str,
) -> PolicyDecision:
    payload = load_acceptance_state()
    accepted = payload.setdefault("accepted_subjects", {})
    assert isinstance(accepted, dict)
    accepted[subject] = {
        "review_fingerprint": str(review_fingerprint or "").strip(),
        "ownership": ownership,
        "legitimacy_status": legitimacy_status,
        "reason": reason,
    }
    _save_acceptance_state(payload)
    current_host = host_id()
    append_audit_event(
        AuditEvent(
            event_type="review_accept",
            subject=subject,
            detail="accepted reviewed subject for local host",
            host_id=current_host,
            evidence_codes=[legitimacy_status],
        )
    )
    return PolicyDecision(
        subject=subject,
        action="accept_review",
        reason=reason,
        severity="low",
        requires_confirmation=False,
        host_id=current_host,
        evidence_codes=[legitimacy_status],
    )


def revoke_subject(subject: str) -> PolicyDecision:
    payload = load_acceptance_state()
    accepted = payload.get("accepted_subjects", {})
    if not isinstance(accepted, dict):
        accepted = {}
    accepted.pop(subject, None)
    payload["accepted_subjects"] = accepted
    _save_acceptance_state(payload)
    current_host = host_id()
    append_audit_event(
        AuditEvent(
            event_type="review_revoke",
            subject=subject,
            detail="revoked reviewed acceptance for local host",
            host_id=current_host,
        )
    )
    return PolicyDecision(
        subject=subject,
        action="revoke_accept_review",
        reason="local accepted-review decision revoked",
        severity="medium",
        requires_confirmation=False,
        host_id=current_host,
    )
