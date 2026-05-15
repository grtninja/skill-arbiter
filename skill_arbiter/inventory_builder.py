from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from .contracts import IncidentRecord, SkillRecord, SourceRecord


def _build_installed_rows(
    module: ModuleType,
    *,
    installed_root: Path,
    openai_baseline: dict[str, object],
    openai_top_level: set[str],
    openai_system: set[str],
    vscode_baseline_additions: set[str],
    vscode_system_additions: set[str],
    third_party_attribution: dict[str, dict[str, str]],
    candidates: set[str],
    recent_work: set[str],
    current_host: str,
) -> tuple[list[SkillRecord], list[IncidentRecord]]:
    skill_rows: list[SkillRecord] = []
    incidents: list[IncidentRecord] = []
    if not installed_root.is_dir():
        return skill_rows, incidents
    for entry in sorted(installed_root.iterdir(), key=lambda item: item.name.lower()):
        if not entry.is_dir():
            continue
        if entry.name == ".system":
            for system_entry in sorted(entry.iterdir(), key=lambda item: item.name.lower()):
                if not system_entry.is_dir():
                    continue
                system_origin = "local_system"
                system_notes: list[str] = []
                if system_entry.name in openai_system:
                    system_origin = "openai_builtin_system"
                elif system_entry.name in vscode_system_additions:
                    system_origin = "vscode_codex_system_baseline_addition"
                    system_notes.append("vscode_codex_system_baseline_addition")
                drift_state = "ok" if system_origin != "local_system" else "local_system_drift"
                risk_class = "trusted" if system_origin != "local_system" else "medium"
                ownership = module._ownership_for_skill(system_entry.name, "installed_system", system_origin)
                legitimacy_status, legitimacy_reason = module._legitimacy_for_skill(ownership, risk_class, [])
                legitimacy_status, legitimacy_reason, review_fingerprint = module._apply_review_acceptance(
                    name=system_entry.name,
                    ownership=ownership,
                    source_type="installed_system",
                    origin=system_origin,
                    drift_state=drift_state,
                    codes=[],
                    legitimacy_status=legitimacy_status,
                    legitimacy_reason=legitimacy_reason,
                )
                skill_rows.append(
                    SkillRecord(
                        name=system_entry.name,
                        source_type="installed_system",
                        origin=system_origin,
                        description=module._read_skill_description(system_entry),
                        local_presence="installed",
                        version_or_commit=str(openai_baseline.get("sha") or ""),
                        drift_state=drift_state,
                        risk_class=module._display_risk_class(legitimacy_status, risk_class),
                        recommended_action=module._recommended_action(legitimacy_status, drift_state, "installed_system"),
                        host_id=current_host,
                        ownership=ownership,
                        legitimacy_status=legitimacy_status,
                        legitimacy_reason=legitimacy_reason,
                        review_fingerprint=review_fingerprint,
                        notes=system_notes,
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
        elif entry.name in vscode_baseline_additions:
            origin = "vscode_codex_baseline_addition"
            notes.append("vscode_codex_baseline_addition")
        elif entry.name not in openai_top_level and entry.name not in vscode_baseline_additions:
            drift_state = "local_only"
            notes.append("installed skill not tracked by overlay or OpenAI baseline")
        if entry.name in openai_top_level:
            origin = "openai_builtin"
            third_party_source_label = ""
            intake_recommendation = ""
        elif third_party_source_label:
            origin = f"third_party_{third_party_source_label}"
            notes.extend(
                [
                    f"third_party_source:{third_party_source_label}",
                    f"third_party_intake:{intake_recommendation or 'unknown'}",
                ]
            )
        severity, codes, details = module._coerce_evaluation(module._evaluate_skill_dir(entry, installed_root))
        ownership = module._ownership_for_skill(
            entry.name,
            "installed_skill",
            origin,
            third_party_source_label=third_party_source_label,
        )
        legitimacy_status, legitimacy_reason = module._legitimacy_for_skill(
            ownership,
            severity,
            codes,
            third_party_source_label=third_party_source_label,
            intake_recommendation=intake_recommendation,
        )
        legitimacy_status, legitimacy_reason, review_fingerprint = module._apply_review_acceptance(
            name=entry.name,
            ownership=ownership,
            source_type="installed_skill",
            origin=origin,
            drift_state=drift_state,
            codes=codes,
            legitimacy_status=legitimacy_status,
            legitimacy_reason=legitimacy_reason,
        )
        displayed_risk = module._display_risk_class(legitimacy_status, severity)
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
        skill_rows.append(
            SkillRecord(
                name=entry.name,
                source_type="installed_skill",
                origin=origin,
                description=module._read_skill_description(entry),
                local_presence="installed",
                version_or_commit=str(openai_baseline.get("sha") or ""),
                drift_state=drift_state,
                risk_class=displayed_risk,
                recommended_action=module._recommended_action(legitimacy_status, drift_state, "installed_skill"),
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
    return skill_rows, incidents


def _append_missing_builtins(
    *,
    skill_rows: list[SkillRecord],
    openai_baseline: dict[str, object],
    openai_top_level: set[str],
    vscode_baseline_additions: set[str],
    current_host: str,
) -> None:
    missing_builtin = sorted(
        (openai_top_level | vscode_baseline_additions) - {row.name for row in skill_rows if row.source_type == "installed_skill"}
    )
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


def _append_candidate_rows(
    *,
    module: ModuleType,
    skill_rows: list[SkillRecord],
    overlay_root: Path,
    candidates: set[str],
    recent_work: set[str],
    third_party_attribution: dict[str, dict[str, str]],
    current_host: str,
) -> None:
    installed_names = {row.name for row in skill_rows}
    for name in sorted(candidates - installed_names):
        skill_dir = overlay_root / name
        attribution = third_party_attribution.get(name, {})
        third_party_source_label = str(attribution.get("source_label") or "").strip()
        intake_recommendation = str(attribution.get("intake_recommendation") or "").strip()
        severity, codes, details = module._coerce_evaluation(module._evaluate_skill_dir(skill_dir, overlay_root))
        ownership = module._ownership_for_skill(
            name,
            "overlay_candidate",
            "skill_candidates",
            third_party_source_label=third_party_source_label,
        )
        legitimacy_status, legitimacy_reason = module._legitimacy_for_skill(
            ownership,
            severity,
            codes,
            third_party_source_label=third_party_source_label,
            intake_recommendation=intake_recommendation,
        )
        legitimacy_status, legitimacy_reason, review_fingerprint = module._apply_review_acceptance(
            name=name,
            ownership=ownership,
            source_type="overlay_candidate",
            origin="skill_candidates",
            drift_state="missing_overlay_install",
            codes=codes,
            legitimacy_status=legitimacy_status,
            legitimacy_reason=legitimacy_reason,
        )
        if module._suppress_candidate_from_active_inventory(
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
                description=module._read_skill_description(skill_dir),
                local_presence="candidate_only",
                version_or_commit="",
                drift_state="missing_overlay_install",
                risk_class=module._display_risk_class(legitimacy_status, severity),
                recommended_action=module._recommended_action(legitimacy_status, "missing_overlay_install", "overlay_candidate"),
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


def _build_source_rows(
    *,
    module: ModuleType,
    current_host: str,
    openai_baseline: dict[str, object],
    openai_top_level: set[str],
    openai_system: set[str],
    recent_work: set[str],
) -> list[SourceRecord]:
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
    source_rows.extend(module._parse_third_party_sources())
    source_rows.extend(module._parse_threat_matrix_sources())
    source_rows.extend(module._parse_skillhub_source_ledger())
    source_rows.extend(module.scan_interop_sources())
    return source_rows


def build_inventory_snapshot(
    module: ModuleType,
    skills_root: Path | None = None,
    candidate_root: Path | None = None,
) -> dict[str, object]:
    installed_root = skills_root or module.DEFAULT_SKILLS_ROOT
    overlay_root = candidate_root or module.DEFAULT_CANDIDATES_ROOT
    current_host = module.host_id()
    openai_baseline = module.fetch_openai_baseline()
    openai_top_level = set(openai_baseline["top_level"])
    openai_system = set(openai_baseline["system"])
    vscode_baseline_additions, vscode_system_additions = module._load_vscode_codex_baseline_additions()
    third_party_attribution = module._parse_third_party_skill_attribution()
    candidates = module._candidate_names(overlay_root)
    recent_work = module._recent_work_skill_names(overlay_root)
    skill_rows, incidents = _build_installed_rows(
        module,
        installed_root=installed_root,
        openai_baseline=openai_baseline,
        openai_top_level=openai_top_level,
        openai_system=openai_system,
        vscode_baseline_additions=vscode_baseline_additions,
        vscode_system_additions=vscode_system_additions,
        third_party_attribution=third_party_attribution,
        candidates=candidates,
        recent_work=recent_work,
        current_host=current_host,
    )
    _append_missing_builtins(
        skill_rows=skill_rows,
        openai_baseline=openai_baseline,
        openai_top_level=openai_top_level,
        vscode_baseline_additions=vscode_baseline_additions,
        current_host=current_host,
    )
    _append_candidate_rows(
        module=module,
        skill_rows=skill_rows,
        overlay_root=overlay_root,
        candidates=candidates,
        recent_work=recent_work,
        third_party_attribution=third_party_attribution,
        current_host=current_host,
    )
    source_rows = _build_source_rows(
        module=module,
        current_host=current_host,
        openai_baseline=openai_baseline,
        openai_top_level=openai_top_level,
        openai_system=openai_system,
        recent_work=recent_work,
    )
    advisor_note = module.request_local_advice(
        "inventory_refresh",
        [code for incident in incidents for code in incident.evidence_codes[:2]],
    )
    legitimacy_summary = module._summary_for_legitimacy(skill_rows)
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
    module.inventory_cache_path().write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return summary


def load_cached_inventory(module: ModuleType) -> dict[str, object]:
    path = module.inventory_cache_path()
    if not path.is_file():
        return build_inventory_snapshot(module)
    return json.loads(path.read_text(encoding="utf-8"))
