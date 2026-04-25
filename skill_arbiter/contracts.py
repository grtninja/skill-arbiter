from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class SkillRecord:
    name: str
    source_type: str
    origin: str
    description: str
    author: str
    canonical_source: str
    local_presence: str
    version_or_commit: str
    drift_state: str
    risk_class: str
    recommended_action: str
    host_id: str
    ownership: str = ""
    legitimacy_status: str = ""
    legitimacy_reason: str = ""
    review_fingerprint: str = ""
    notes: list[str] = field(default_factory=list)
    finding_codes: list[str] = field(default_factory=list)
    finding_details: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceRecord:
    source_id: str
    source_type: str
    origin: str
    version_or_commit: str
    local_presence: str
    drift_state: str
    risk_class: str
    recommended_action: str
    host_id: str
    remote_url: str = ""
    compatibility_surface: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IncidentRecord:
    incident_id: str
    category: str
    severity: str
    subject: str
    summary: str
    host_id: str
    requires_confirmation: bool
    ownership: str = ""
    legitimacy_status: str = ""
    evidence_codes: list[str] = field(default_factory=list)
    finding_details: list[dict[str, str]] = field(default_factory=list)
    recommended_steps: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyDecision:
    subject: str
    action: str
    reason: str
    severity: str
    requires_confirmation: bool
    host_id: str
    evidence_codes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrivacyFinding:
    path: str
    line: int
    col: int
    kind: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelfGovernanceFinding:
    severity: str
    code: str
    message: str
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    event_type: str
    subject: str
    detail: str
    host_id: str
    requires_confirmation: bool = False
    evidence_codes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborationEvent:
    event_id: str
    task: str
    outcome: str
    host_id: str
    collaborators: list[str] = field(default_factory=list)
    repo_scope: list[str] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    proposed_skill_work: list[dict[str, str]] = field(default_factory=list)
    note: str = ""
    stability: str = "emerging"
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuestCheckpoint:
    checkpoint_id: str
    label: str
    status: str
    summary: str = ""
    evidence: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuestStep:
    step_id: str
    label: str
    status: str
    skills: list[str] = field(default_factory=list)
    summary: str = ""
    checkpoint_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuestRecord:
    quest_id: str
    chain_id: str
    title: str
    request: str
    outcome: str
    host_id: str
    required_skills: list[str] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    repo_scope: list[str] = field(default_factory=list)
    meta_harness: bool = False
    final_outcome: str = ""
    deliverables: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    checkpoints: list[QuestCheckpoint] = field(default_factory=list)
    steps: list[QuestStep] = field(default_factory=list)
    skill_xp_awards: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checkpoints"] = [item.to_dict() for item in self.checkpoints]
        payload["steps"] = [item.to_dict() for item in self.steps]
        return payload


@dataclass
class MitigationStep:
    step_id: str
    label: str
    status: str
    summary: str
    requires_confirmation: bool = False
    auto_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MitigationCase:
    case_id: str
    subject: str
    classification: str
    severity: str
    source_domain: str
    hostile: bool
    rebuildable: bool
    summary: str
    operator_summary: str = ""
    recommended_path: str = ""
    finding_codes: list[str] = field(default_factory=list)
    evidence_codes: list[str] = field(default_factory=list)
    finding_details: list[dict[str, str]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    steps: list[MitigationStep] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["steps"] = [step.to_dict() for step in self.steps]
        return payload
