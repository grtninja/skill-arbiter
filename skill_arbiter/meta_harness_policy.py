from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


SCAN_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".ps1", ".txt", ".env", ".json"}
LEGACY_REPO_ROOT_RE = re.compile(r"(?i)(?:c:\\users\\eddie\\documents\\github|documents\\github)")
LEGACY_REPO_ROOT_CONTEXT_ALLOW_RE = re.compile(
    r"normalize[^\n\r]{0,160}G:\\GitHub|"
    r"canonical[^\n\r]{0,160}G:\\GitHub|"
    r"Documents\\GitHub[^\n\r]{0,160}(?:alias|normalize|G:\\GitHub)",
    re.IGNORECASE,
)
NON_AUTHORITATIVE_1234_RE = re.compile(r"http://127\.0\.0\.1:1234(?:/[^\s`\"']*)?", re.IGNORECASE)
NON_AUTHORITATIVE_ALLOW_RE = re.compile(r"non-authoritative|operator surface", re.IGNORECASE)


@dataclass(frozen=True)
class MetaHarnessFinding:
    skill: str
    path: str
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "skill": self.skill,
            "path": self.path,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class RequiredPattern:
    relative_path: str
    severity: str
    code: str
    pattern: str
    message: str


REQUIRED_PATTERNS: tuple[RequiredPattern, ...] = (
    RequiredPattern(
        relative_path="skill-hub/SKILL.md",
        severity="medium",
        code="local_subagent_policy_missing",
        pattern=r"local OpenClaw-compatible subagents.*preferred|prefer.*local OpenClaw-compatible subagents",
        message="Skill Hub must prefer healthy local OpenClaw-compatible subagents before cloud sidecars.",
    ),
    RequiredPattern(
        relative_path="skill-hub/SKILL.md",
        severity="medium",
        code="cloud_sidecar_budget_policy_missing",
        pattern=r"lower[- ]reasoning.*low[- ]cost sidecar|low[- ]cost sidecar.*lower[- ]reasoning",
        message="Skill Hub must describe cloud sidecars as lower-reasoning, low-cost lanes.",
    ),
    RequiredPattern(
        relative_path="multitask-orchestrator/SKILL.md",
        severity="medium",
        code="multitask_local_subagent_policy_missing",
        pattern=r"local OpenClaw-compatible subagents.*preferred",
        message="Multitask Orchestrator must prefer healthy local OpenClaw-compatible subagents before cloud sidecars.",
    ),
    RequiredPattern(
        relative_path="skills-discovery-curation/SKILL.md",
        severity="medium",
        code="curation_meta_harness_authority_missing",
        pattern=r"127\.0\.0\.1:2337|2337",
        message="Skills Discovery and Curation must record the hosted 27B lane at :2337 when handling meta-harness work.",
    ),
    RequiredPattern(
        relative_path="skills-discovery-curation/SKILL.md",
        severity="medium",
        code="curation_pc_control_evidence_missing",
        pattern=r"PC Control",
        message="Skills Discovery and Curation must mention PC Control evidence for meta-harness curation lanes.",
    ),
    RequiredPattern(
        relative_path="local-compute-usage/SKILL.md",
        severity="medium",
        code="canonical_root_contract_missing",
        pattern=r"G:\\GitHub",
        message="Local Compute Usage must reference the canonical G:\\GitHub root contract.",
    ),
    RequiredPattern(
        relative_path="heterogeneous-stack-validation/SKILL.md",
        severity="medium",
        code="hosted_lane_missing",
        pattern=r"127\.0\.0\.1:2337",
        message="Heterogeneous Stack Validation must include the hosted 27B lane at :2337.",
    ),
    RequiredPattern(
        relative_path="heterogeneous-stack-validation/SKILL.md",
        severity="medium",
        code="lmstudio_operator_surface_missing",
        pattern=r"(LM Studio|1234).*(non-authoritative|operator surface)|(non-authoritative|operator surface).*(LM Studio|1234)",
        message="Heterogeneous Stack Validation must describe LM Studio :1234 as a non-authoritative operator surface when mentioned.",
    ),
    RequiredPattern(
        relative_path="shim-pc-control-brain-routing/SKILL.md",
        severity="high",
        code="shim_hosted_lane_missing",
        pattern=r"127\.0\.0\.1:2337",
        message="Shim PC Control Brain Routing must include the hosted 27B lane at :2337 in its authority contract.",
    ),
    RequiredPattern(
        relative_path="shim-pc-control-brain-routing/SKILL.md",
        severity="high",
        code="shim_pc_control_local_agent_missing",
        pattern=r"PC Control local-agent|PC Control .*status surface",
        message="Shim PC Control Brain Routing must require PC Control local-agent or status-surface evidence before sidecar research.",
    ),
    RequiredPattern(
        relative_path="shim-pc-control-brain-routing/SKILL.md",
        severity="medium",
        code="shim_canonical_root_missing",
        pattern=r"G:\\GitHub",
        message="Shim PC Control Brain Routing must normalize repo roots to G:\\GitHub.",
    ),
    RequiredPattern(
        relative_path="repo-b-wsl-hybrid-ops/SKILL.md",
        severity="medium",
        code="wsl_hosted_lane_missing",
        pattern=r"127\.0\.0\.1:2337",
        message="REPO_B WSL Hybrid Ops must validate the hosted 27B lane at :2337 instead of relying on LM Studio :1234.",
    ),
)


def _iter_candidate_files(skills_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in skills_root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def _skill_name_from_path(skills_root: Path, path: Path) -> str:
    try:
        return path.relative_to(skills_root).parts[0]
    except Exception:
        return ""


def scan_candidate_meta_harness(skills_root: Path) -> list[MetaHarnessFinding]:
    root = Path(skills_root).expanduser().resolve()
    if not root.is_dir():
        return []

    findings: list[MetaHarnessFinding] = []
    seen: set[tuple[str, str, str]] = set()
    files = _iter_candidate_files(root)

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relative_path = path.relative_to(root).as_posix()
        skill = _skill_name_from_path(root, path)

        if LEGACY_REPO_ROOT_RE.search(text) and not LEGACY_REPO_ROOT_CONTEXT_ALLOW_RE.search(text):
            row = (skill, relative_path, "legacy_repo_root_alias")
            if row not in seen:
                seen.add(row)
                findings.append(
                    MetaHarnessFinding(
                        skill=skill,
                        path=relative_path,
                        severity="high",
                        code="legacy_repo_root_alias",
                        message="Legacy Documents\\GitHub root is present; normalize to the canonical G:\\GitHub root contract.",
                    )
                )

        if NON_AUTHORITATIVE_1234_RE.search(text) and not NON_AUTHORITATIVE_ALLOW_RE.search(text):
            row = (skill, relative_path, "non_authoritative_1234_authority")
            if row not in seen:
                seen.add(row)
                findings.append(
                    MetaHarnessFinding(
                        skill=skill,
                        path=relative_path,
                        severity="high",
                        code="non_authoritative_1234_authority",
                        message="LM Studio :1234 is referenced as an authority surface without non-authoritative/operator-surface framing.",
                    )
                )

    for rule in REQUIRED_PATTERNS:
        path = root / Path(rule.relative_path)
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(rule.pattern, text, flags=re.IGNORECASE | re.DOTALL):
            continue
        skill = _skill_name_from_path(root, path)
        relative_path = path.relative_to(root).as_posix()
        row = (skill, relative_path, rule.code)
        if row in seen:
            continue
        seen.add(row)
        findings.append(
            MetaHarnessFinding(
                skill=skill,
                path=relative_path,
                severity=rule.severity,
                code=rule.code,
                message=rule.message,
            )
        )

    return findings


def findings_for_skill(skills_root: Path, skill_name: str) -> list[MetaHarnessFinding]:
    target = str(skill_name or "").strip()
    if not target:
        return []
    return [item for item in scan_candidate_meta_harness(skills_root) if item.skill == target]
