from __future__ import annotations

import hashlib

from .accepted_risk import subject_is_accepted
from .contracts import SkillRecord
from .threat_catalog import ALWAYS_BLOCK_CODES, HOSTILE_CODES


def _ownership_for_skill(
    name: str,
    source_type: str,
    origin: str,
    *,
    third_party_source_label: str = "",
) -> str:
    if origin in {"openai_builtin", "openai_builtin_system"}:
        return "official_builtin"
    if origin in {"vscode_codex_baseline_addition", "vscode_codex_system_baseline_addition"}:
        return "baseline_addition"
    if third_party_source_label:
        return "third_party_candidate" if source_type == "overlay_candidate" else "third_party_imported"
    if source_type == "overlay_candidate":
        return "repo_owned_candidate"
    if origin == "overlay_candidate_installed":
        return "repo_owned"
    if source_type == "installed_system":
        return "local_system"
    if source_type == "openai_builtin_baseline":
        return "official_baseline_missing"
    if source_type == "installed_skill":
        return "local_unowned"
    return "unknown"


def _legitimacy_for_skill(
    ownership: str,
    severity: str,
    codes: list[str],
    *,
    third_party_source_label: str = "",
    intake_recommendation: str = "",
) -> tuple[str, str]:
    if any(code in ALWAYS_BLOCK_CODES for code in codes):
        return "blocked_hostile", "Hostile signatures detected in the skill content."
    if ownership == "official_builtin":
        return "official_trusted", "Matches the official OpenAI/Codex baseline and is accepted by baseline policy on this host."
    if ownership == "baseline_addition":
        return "owned_trusted", "Matches a host-recognized VS Code Codex baseline addition without claiming upstream OpenAI ownership."
    if ownership in {"repo_owned", "repo_owned_candidate"}:
        return "owned_trusted", "Owned by the local stack and accepted by local ownership policy on this host."
    if ownership in {"third_party_imported", "third_party_candidate"}:
        normalized_intake = intake_recommendation.strip().lower()
        if normalized_intake == "reject":
            return "blocked_hostile", (
                f"Third-party intake rejected this {third_party_source_label or 'external'} skill; "
                "keep it quarantined or remove it from the installed stack."
            )
        if any(code in HOSTILE_CODES for code in codes):
            return "blocked_hostile", (
                f"Imported third-party skill from {third_party_source_label or 'external'} hit explicit hostile signatures."
            )
        if ownership == "third_party_candidate":
            return "third_party_watch", (
                f"Third-party candidate from {third_party_source_label or 'external'} is not installed and stays on the research/watchlist lane."
            )
        if normalized_intake in {"admit", "accepted", "keep"}:
            return "third_party_trusted", (
                f"Installed third-party skill from {third_party_source_label or 'external'} remains provenance-tracked and accepted for local use."
            )
        return "third_party_watch", (
            f"Installed third-party skill from {third_party_source_label or 'external'} remains watchlisted until a trusted local replacement exists."
        )
    if ownership == "local_system":
        return "baseline_review", "Local system skill is present but not yet reconciled to the official baseline."
    if ownership == "official_baseline_missing":
        return "baseline_gap", "Official baseline skill is missing locally and should be reconciled."
    return "manual_review", "Unowned or locally drifted skill requires operator review."


def _review_fingerprint(*, name: str, ownership: str, source_type: str, origin: str, drift_state: str, codes: list[str]) -> str:
    raw = "|".join(
        [
            name,
            ownership,
            source_type,
            origin,
            drift_state,
            ",".join(sorted(dict.fromkeys(codes))),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _apply_review_acceptance(
    *,
    name: str,
    ownership: str,
    source_type: str,
    origin: str,
    drift_state: str,
    codes: list[str],
    legitimacy_status: str,
    legitimacy_reason: str,
) -> tuple[str, str, str]:
    review_fingerprint = _review_fingerprint(
        name=name,
        ownership=ownership,
        source_type=source_type,
        origin=origin,
        drift_state=drift_state,
        codes=codes,
    )
    if not subject_is_accepted(name, review_fingerprint):
        return legitimacy_status, legitimacy_reason, review_fingerprint
    status_map = {
        "official_sensitive": "official_accepted",
        "official_review": "official_accepted",
        "owned_sensitive": "owned_accepted",
        "owned_review": "owned_accepted",
        "manual_review": "manual_accepted",
    }
    accepted_status = status_map.get(legitimacy_status, legitimacy_status)
    if accepted_status == legitimacy_status:
        return legitimacy_status, legitimacy_reason, review_fingerprint
    accepted_reason = (
        f"{legitimacy_reason.rstrip()} Local operator review accepted this subject on the current host; "
        "keep guardrails, auditability, and deterministic startup constraints in force."
    )
    return accepted_status, accepted_reason, review_fingerprint


def _display_risk_class(legitimacy_status: str, raw_severity: str) -> str:
    if legitimacy_status == "blocked_hostile":
        return "critical"
    if legitimacy_status in {"official_sensitive", "owned_sensitive"}:
        return "high"
    if legitimacy_status == "third_party_watch":
        return "monitor"
    if legitimacy_status == "third_party_trusted":
        return "monitor" if raw_severity == "low" else "low"
    if legitimacy_status in {"manual_review", "official_review", "owned_review"}:
        return "high" if raw_severity == "critical" else "medium"
    if legitimacy_status in {"official_accepted", "owned_accepted", "manual_accepted"}:
        return "accepted"
    if legitimacy_status == "baseline_review":
        return "medium"
    if legitimacy_status == "baseline_gap":
        return "monitor"
    if legitimacy_status in {"official_trusted", "owned_trusted"}:
        return "trusted" if raw_severity == "low" else "low"
    return raw_severity


def _recommended_action(legitimacy_status: str, drift_state: str, source_type: str) -> str:
    if legitimacy_status == "blocked_hostile":
        return "quarantine"
    if legitimacy_status == "baseline_gap":
        return "reconcile_baseline"
    if legitimacy_status == "third_party_trusted":
        return "keep"
    if legitimacy_status == "third_party_watch":
        return "audit_before_admit" if source_type == "overlay_candidate" else "keep"
    if legitimacy_status in {"official_accepted", "owned_accepted", "manual_accepted"}:
        return "keep"
    if legitimacy_status in {"official_trusted", "owned_trusted"} and drift_state == "ok":
        return "install_candidate" if source_type == "overlay_candidate" else "keep"
    return "review"


def _suppress_candidate_from_active_inventory(*, ownership: str, legitimacy_status: str, local_presence: str) -> bool:
    return (
        local_presence == "candidate_only"
        and ownership == "third_party_candidate"
        and legitimacy_status in {"blocked_hostile", "third_party_watch"}
    )


def _summary_for_legitimacy(skills: list[SkillRecord]) -> dict[str, int]:
    rows = [
        item.legitimacy_status
        for item in skills
        if item.local_presence in {"installed", "missing"}
    ]
    return {
        "official_trusted": sum(1 for item in rows if item == "official_trusted"),
        "owned_trusted": sum(1 for item in rows if item == "owned_trusted"),
        "accepted_review": sum(1 for item in rows if item in {"official_accepted", "owned_accepted", "manual_accepted"}),
        "needs_review": sum(1 for item in rows if item in {"official_review", "official_sensitive", "owned_review", "owned_sensitive", "baseline_review", "manual_review"}),
        "blocked_hostile": sum(1 for item in rows if item == "blocked_hostile"),
    }
