from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

from .accepted_risk import subject_is_accepted
from .contracts import IncidentRecord, SkillRecord, SourceRecord
from .interop import scan_interop_sources
from .llm_advisor import request_local_advice
from .paths import DEFAULT_CANDIDATES_ROOT, DEFAULT_SKILLS_ROOT, REPO_ROOT, host_id, inventory_cache_path
from .threat_catalog import ALWAYS_BLOCK_CODES, HOSTILE_CODES, SAFE_CAPABILITY_CODES, describe_codes
from supply_chain_guard import scan_skill_dir_content, scan_skill_tree, summarize_findings

THIRD_PARTY_SOURCE_ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$")
THREAT_MATRIX_ROW_RE = re.compile(r"^\| `?([^|`]+?)`? \| `([^`]+)` \| ([^|]+) \| `([^`]+)` \| (.+?) \|$")
THIRD_PARTY_SKILL_ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$")


def _read_skill_description(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ""
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"(?s)^---\n(.*?)\n---\n?", text)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _risk_from_codes(summary: dict[str, object]) -> tuple[str, list[str]]:
    findings = summary.get("findings", [])
    codes = list(dict.fromkeys(row["code"] for row in findings if isinstance(row, dict) and "code" in row))
    blocker_count = int(summary.get("blocker_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    if blocker_count:
        return "critical", codes
    if warning_count:
        return "high", codes
    return "low", codes


def _evaluate_skill_dir(skill_dir: Path, source_root: Path) -> tuple[str, list[str], list[dict[str, str]]]:
    content_summary = summarize_findings(scan_skill_dir_content(skill_dir))
    tree_summary = summarize_findings(scan_skill_tree(skill_dir, source_root))
    findings = list(content_summary["findings"]) + list(tree_summary["findings"])
    severity, codes = _risk_from_codes(
        {
            "blocker_count": int(content_summary["blocker_count"]) + int(tree_summary["blocker_count"]),
            "warning_count": int(content_summary["warning_count"]) + int(tree_summary["warning_count"]),
            "findings": findings,
        }
    )
    detail_by_code = {item["code"]: item for item in findings if isinstance(item, dict) and item.get("code")}
    details = []
    for descriptor in describe_codes(codes):
        message = ""
        finding = detail_by_code.get(descriptor["code"])
        if finding:
            message = str(finding.get("message") or "")
        details.append({**descriptor, "message": message})
    return severity, codes, details


def _coerce_evaluation(result: tuple[object, ...]) -> tuple[str, list[str], list[dict[str, str]]]:
    if len(result) == 3:
        severity, codes, details = result
        return str(severity), list(codes), list(details)
    severity, codes = result
    return str(severity), list(codes), describe_codes(list(codes))


def _parse_third_party_skill_attribution() -> dict[str, dict[str, str]]:
    path = REPO_ROOT / "references" / "third-party-skill-attribution.md"
    if not path.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = THIRD_PARTY_SKILL_ROW_RE.match(line.strip())
        if not match:
            continue
        local_name, origin_skill, source_label, intake_recommendation, origin_path = match.groups()
        rows[local_name] = {
            "origin_skill": origin_skill,
            "source_label": source_label,
            "intake_recommendation": intake_recommendation,
            "origin_path": origin_path,
        }
    return rows


def _ownership_for_skill(
    name: str,
    source_type: str,
    origin: str,
    *,
    third_party_source_label: str = "",
) -> str:
    if origin in {"openai_builtin", "openai_builtin_system"}:
        return "official_builtin"
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
        and legitimacy_status == "blocked_hostile"
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


def _fetch_github_dirs(repo: str, path: str = "") -> tuple[list[str], str]:
    api_url = f"https://api.github.com/repos/{repo}/contents"
    if path:
        api_url += f"/{path.strip('/')}"
    req = request.Request(api_url, headers={"User-Agent": "skill-arbiter-nullclaw"})
    with request.urlopen(req, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    names = [item["name"] for item in payload if item.get("type") == "dir" and not str(item.get("name", "")).startswith("_")]
    sha = str(payload[0].get("sha", ""))[:12] if payload else ""
    return sorted(names), sha


def fetch_openai_baseline() -> dict[str, object]:
    try:
        top_level, sha = _fetch_github_dirs("openai/skills", "skills/.curated")
        try:
            system, _ = _fetch_github_dirs("openai/skills", "skills/.system")
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError):
            system = []
        return {"top_level": top_level, "system": system, "sha": sha, "status": "online"}
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError):
        return {"top_level": [], "system": [], "sha": "", "status": "offline"}


def _parse_third_party_sources() -> list[SourceRecord]:
    path = REPO_ROOT / "references" / "third-party-skill-attribution.md"
    if not path.is_file():
        return []
    rows: list[SourceRecord] = []
    current_host = host_id()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = THIRD_PARTY_SOURCE_ROW_RE.match(line.strip())
        if not match:
            continue
        label, source_root, repo_root, commit, remote, _license = match.groups()
        rows.append(
            SourceRecord(
                source_id=label,
                source_type="curated_third_party",
                origin=source_root,
                version_or_commit=commit,
                local_presence="tracked_reference",
                drift_state="tracked",
                risk_class="high" if "nullclaw" not in label else "medium",
                recommended_action="manual_review",
                host_id=current_host,
                remote_url=remote,
                notes=[repo_root],
            )
        )
    return rows


def _parse_threat_matrix_sources() -> list[SourceRecord]:
    path = REPO_ROOT / "references" / "OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md"
    if not path.is_file():
        return []
    rows: list[SourceRecord] = []
    current_host = host_id()
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = THREAT_MATRIX_ROW_RE.match(line.strip())
        if not match:
            continue
        label, url_text, classification, risk_class, note = match.groups()
        source_id = label.strip().replace(" ", "_").lower()
        if source_id in seen:
            continue
        seen.add(source_id)
        rows.append(
            SourceRecord(
                source_id=source_id,
                source_type="curated_catalog",
                origin=classification.strip(),
                version_or_commit="",
                local_presence="reference_only",
                drift_state="tracked",
                risk_class=risk_class.strip(),
                recommended_action="manual_review" if risk_class.strip() in {"high", "critical"} else "monitor",
                host_id=current_host,
                remote_url=url_text,
                notes=[note.strip()],
            )
        )
    return rows


def _candidate_names(candidate_root: Path) -> set[str]:
    if not candidate_root.is_dir():
        return set()
    return {item.name for item in candidate_root.iterdir() if item.is_dir()}


def _recent_work_skill_names(candidate_root: Path) -> set[str]:
    refs = sorted((REPO_ROOT / "references").glob("cross_repo_open_work_radar_*.json"))
    if not refs:
        return set()
    payload = refs[-1].read_text(encoding="utf-8", errors="ignore")
    return {name for name in _candidate_names(candidate_root) if name in payload}


def build_inventory_snapshot(
    skills_root: Path | None = None,
    candidate_root: Path | None = None,
) -> dict[str, object]:
    installed_root = skills_root or DEFAULT_SKILLS_ROOT
    overlay_root = candidate_root or DEFAULT_CANDIDATES_ROOT
    current_host = host_id()
    openai_baseline = fetch_openai_baseline()
    openai_top_level = set(openai_baseline["top_level"])
    openai_system = set(openai_baseline["system"])
    third_party_attribution = _parse_third_party_skill_attribution()
    candidates = _candidate_names(overlay_root)
    recent_work = _recent_work_skill_names(overlay_root)

    skill_rows: list[SkillRecord] = []
    incidents: list[IncidentRecord] = []

    if installed_root.is_dir():
        for entry in sorted(installed_root.iterdir(), key=lambda item: item.name.lower()):
            if not entry.is_dir():
                continue
            if entry.name == ".system":
                for system_entry in sorted(entry.iterdir(), key=lambda item: item.name.lower()):
                    if not system_entry.is_dir():
                        continue
                    drift_state = "ok" if system_entry.name in openai_system else "local_system_drift"
                    risk_class = "trusted" if system_entry.name in openai_system else "medium"
                    ownership = _ownership_for_skill(system_entry.name, "installed_system", "openai_builtin_system" if system_entry.name in openai_system else "local_system")
                    legitimacy_status, legitimacy_reason = _legitimacy_for_skill(ownership, risk_class, [])
                    legitimacy_status, legitimacy_reason, review_fingerprint = _apply_review_acceptance(
                        name=system_entry.name,
                        ownership=ownership,
                        source_type="installed_system",
                        origin="openai_builtin_system" if system_entry.name in openai_system else "local_system",
                        drift_state=drift_state,
                        codes=[],
                        legitimacy_status=legitimacy_status,
                        legitimacy_reason=legitimacy_reason,
                    )
                    displayed_risk = _display_risk_class(legitimacy_status, risk_class)
                    system_action = _recommended_action(legitimacy_status, drift_state, "installed_system")
                    skill_rows.append(
                        SkillRecord(
                            name=system_entry.name,
                            source_type="installed_system",
                            origin="openai_builtin_system" if system_entry.name in openai_system else "local_system",
                            description=_read_skill_description(system_entry),
                            local_presence="installed",
                            version_or_commit=str(openai_baseline.get("sha") or ""),
                            drift_state=drift_state,
                            risk_class=displayed_risk,
                            recommended_action=system_action,
                            host_id=current_host,
                            ownership=ownership,
                            legitimacy_status=legitimacy_status,
                            legitimacy_reason=legitimacy_reason,
                            review_fingerprint=review_fingerprint,
                        )
                    )
                continue
            risk_class = "trusted" if entry.name in openai_top_level else "medium"
            origin = "openai_builtin" if entry.name in openai_top_level else "overlay_or_local"
            drift_state = "ok"
            notes: list[str] = []
            attribution = third_party_attribution.get(entry.name, {})
            third_party_source_label = str(attribution.get("source_label") or "").strip()
            intake_recommendation = str(attribution.get("intake_recommendation") or "").strip()
            if entry.name in candidates:
                origin = "overlay_candidate_installed"
            elif entry.name not in openai_top_level:
                drift_state = "local_only"
                notes.append("installed skill not tracked by overlay or OpenAI baseline")
            if third_party_source_label:
                origin = f"third_party_{third_party_source_label}"
                notes.extend(
                    [
                        f"third_party_source:{third_party_source_label}",
                        f"third_party_intake:{intake_recommendation or 'unknown'}",
                    ]
                )
            severity, codes, details = _coerce_evaluation(_evaluate_skill_dir(entry, installed_root))
            ownership = _ownership_for_skill(
                entry.name,
                "installed_skill",
                origin,
                third_party_source_label=third_party_source_label,
            )
            legitimacy_status, legitimacy_reason = _legitimacy_for_skill(
                ownership,
                severity,
                codes,
                third_party_source_label=third_party_source_label,
                intake_recommendation=intake_recommendation,
            )
            legitimacy_status, legitimacy_reason, review_fingerprint = _apply_review_acceptance(
                name=entry.name,
                ownership=ownership,
                source_type="installed_skill",
                origin=origin,
                drift_state=drift_state,
                codes=codes,
                legitimacy_status=legitimacy_status,
                legitimacy_reason=legitimacy_reason,
            )
            displayed_risk = _display_risk_class(legitimacy_status, severity)
            if displayed_risk in {"critical", "high"}:
                recommended_steps = ["quarantine", "audit_vectors", "audit_sources"]
                if legitimacy_status in {"official_review", "official_sensitive", "owned_review", "owned_sensitive"}:
                    recommended_steps = ["request", "audit_vectors", "repeat"]
                if legitimacy_status == "blocked_hostile":
                    recommended_steps = ["quarantine", "blacklist", "remove_or_refactor", "repeat"]
                incidents.append(
                    IncidentRecord(
                        incident_id=f"installed-{entry.name}",
                        category="skill_risk",
                        severity=displayed_risk,
                        subject=entry.name,
                        summary=f"installed skill has {displayed_risk} host-security findings",
                        host_id=current_host,
                        requires_confirmation=False,
                        ownership=ownership,
                        legitimacy_status=legitimacy_status,
                        evidence_codes=codes,
                        finding_details=details,
                        recommended_steps=recommended_steps,
                    )
                )
            installed_action = _recommended_action(legitimacy_status, drift_state, "installed_skill")
            skill_rows.append(
                SkillRecord(
                    name=entry.name,
                    source_type="installed_skill",
                    origin=origin,
                    description=_read_skill_description(entry),
                    local_presence="installed",
                    version_or_commit=str(openai_baseline.get("sha") or ""),
                    drift_state=drift_state,
                    risk_class=displayed_risk,
                    recommended_action=installed_action,
                    host_id=current_host,
                    ownership=ownership,
                    legitimacy_status=legitimacy_status,
                    legitimacy_reason=legitimacy_reason,
                    review_fingerprint=review_fingerprint,
                    notes=notes + (["recent_work_relevant"] if entry.name in recent_work else []),
                    finding_codes=codes,
                    finding_details=details,
                )
            )

    missing_builtin = sorted(openai_top_level - {row.name for row in skill_rows if row.source_type == "installed_skill"})
    for name in missing_builtin:
        skill_rows.append(
            SkillRecord(
                name=name,
                source_type="openai_builtin_baseline",
                origin="openai_builtin",
                description="",
                local_presence="missing",
                version_or_commit=str(openai_baseline.get("sha") or ""),
                drift_state="missing_local_builtin",
                risk_class="trusted",
                recommended_action="monitor",
                host_id=current_host,
                ownership="official_baseline_missing",
                legitimacy_status="baseline_gap",
                legitimacy_reason="Official baseline skill is missing locally and should be reconciled.",
            )
        )

    installed_names = {row.name for row in skill_rows}
    for name in sorted(candidates - installed_names):
        skill_dir = overlay_root / name
        attribution = third_party_attribution.get(name, {})
        third_party_source_label = str(attribution.get("source_label") or "").strip()
        intake_recommendation = str(attribution.get("intake_recommendation") or "").strip()
        severity, codes, details = _coerce_evaluation(_evaluate_skill_dir(skill_dir, overlay_root))
        ownership = _ownership_for_skill(
            name,
            "overlay_candidate",
            "skill_candidates",
            third_party_source_label=third_party_source_label,
        )
        legitimacy_status, legitimacy_reason = _legitimacy_for_skill(
            ownership,
            severity,
            codes,
            third_party_source_label=third_party_source_label,
            intake_recommendation=intake_recommendation,
        )
        legitimacy_status, legitimacy_reason, review_fingerprint = _apply_review_acceptance(
            name=name,
            ownership=ownership,
            source_type="overlay_candidate",
            origin="skill_candidates",
            drift_state="missing_overlay_install",
            codes=codes,
            legitimacy_status=legitimacy_status,
            legitimacy_reason=legitimacy_reason,
        )
        displayed_risk = _display_risk_class(legitimacy_status, severity)
        recommended = _recommended_action(legitimacy_status, "missing_overlay_install", "overlay_candidate")
        if _suppress_candidate_from_active_inventory(
            ownership=ownership,
            legitimacy_status=legitimacy_status,
            local_presence="candidate_only",
        ):
            continue
        skill_rows.append(
            SkillRecord(
                name=name,
                source_type="overlay_candidate",
                origin="skill_candidates",
                description=_read_skill_description(skill_dir),
                local_presence="candidate_only",
                version_or_commit="",
                drift_state="missing_overlay_install",
                risk_class=displayed_risk,
                recommended_action=recommended,
                host_id=current_host,
                ownership=ownership,
                legitimacy_status=legitimacy_status,
                    legitimacy_reason=legitimacy_reason,
                    review_fingerprint=review_fingerprint,
                notes=(
                    (["recent_work_relevant"] if name in recent_work else [])
                    + ([f"third_party_source:{third_party_source_label}"] if third_party_source_label else [])
                    + ([f"third_party_intake:{intake_recommendation}"] if intake_recommendation else [])
                ),
                finding_codes=codes,
                finding_details=details,
            )
        )

    source_rows: list[SourceRecord] = [
        SourceRecord(
            source_id="local-installed",
            source_type="local",
            origin="$CODEX_HOME/skills",
            version_or_commit="",
            local_presence="present",
            drift_state="tracked",
            risk_class="monitor",
            recommended_action="observe",
            host_id=current_host,
            compatibility_surface="local",
            notes=["current local Codex skills root"],
        ),
        SourceRecord(
            source_id="skill-candidates",
            source_type="overlay",
            origin="skill-candidates",
            version_or_commit="git-tracked",
            local_presence="present",
            drift_state="tracked",
            risk_class="monitor",
            recommended_action="audit_before_admit",
            host_id=current_host,
            compatibility_surface="repo_overlay",
            notes=["public-shape overlay candidates"],
        ),
        SourceRecord(
            source_id="openai-skills",
            source_type="official_upstream",
            origin="openai/skills",
            version_or_commit=str(openai_baseline.get("sha") or ""),
            local_presence="online" if openai_baseline.get("status") == "online" else "offline",
            drift_state="tracked",
            risk_class="trusted",
            recommended_action="reconcile_baseline",
            host_id=current_host,
            remote_url="https://github.com/openai/skills",
            compatibility_surface="official_baseline",
            notes=[f"top_level={len(openai_top_level)}", f"system={len(openai_system)}"],
        ),
    ]
    if recent_work:
        source_rows.append(
            SourceRecord(
                source_id="cross-repo-radar",
                source_type="recent_work",
                origin="references/cross_repo_open_work_radar_*.json",
                version_or_commit="latest",
                local_presence="present",
                drift_state="tracked",
                risk_class="monitor",
                recommended_action="prioritize_recent_work",
                host_id=current_host,
                compatibility_surface="cross_repo",
                notes=[f"recent_work_skills={len(recent_work)}"],
            )
        )
    source_rows.extend(_parse_third_party_sources())
    source_rows.extend(_parse_threat_matrix_sources())
    source_rows.extend(scan_interop_sources())

    advisor_note = request_local_advice(
        "inventory_refresh",
        [code for incident in incidents for code in incident.evidence_codes[:2]],
    )
    legitimacy_summary = _summary_for_legitimacy(skill_rows)
    interop_sources = [row.to_dict() for row in source_rows if row.source_type == "interop_surface"]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_id": current_host,
        "skill_count": len(skill_rows),
        "source_count": len(source_rows),
        "incident_count": len(incidents),
        "recent_work_skills": sorted(recent_work),
        "legitimacy_summary": legitimacy_summary,
        "interop_sources": interop_sources,
        "advisor_note": advisor_note,
        "skills": [row.to_dict() for row in sorted(skill_rows, key=lambda item: (item.source_type, item.name))],
        "sources": [row.to_dict() for row in source_rows],
        "incidents": [row.to_dict() for row in incidents],
    }
    inventory_cache_path().write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return summary


def load_cached_inventory() -> dict[str, object]:
    path = inventory_cache_path()
    if not path.is_file():
        return build_inventory_snapshot()
    return json.loads(path.read_text(encoding="utf-8"))
