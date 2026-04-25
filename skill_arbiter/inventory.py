from __future__ import annotations

import sys

from . import inventory_baselines as _baselines
from . import inventory_builder as _builder
from . import inventory_evaluation as _evaluation
from . import inventory_policy as _policy
from .paths import REPO_ROOT, host_id


_safe_load_radar_payload = _baselines._safe_load_radar_payload
_extract_tokens_from_path = _baselines._extract_tokens_from_path
_extract_tokens_from_subject = _baselines._extract_tokens_from_subject
_candidate_names_from_radar = _baselines._candidate_names_from_radar
_candidate_names = _baselines._candidate_names

_read_skill_frontmatter = _evaluation._read_skill_frontmatter
_read_skill_description = _evaluation._read_skill_description
_risk_from_codes = _evaluation._risk_from_codes
_evaluate_skill_dir = _evaluation._evaluate_skill_dir
_coerce_evaluation = _evaluation._coerce_evaluation

_ownership_for_skill = _policy._ownership_for_skill
_legitimacy_for_skill = _policy._legitimacy_for_skill
_review_fingerprint = _policy._review_fingerprint
_apply_review_acceptance = _policy._apply_review_acceptance
_display_risk_class = _policy._display_risk_class
_recommended_action = _policy._recommended_action
_suppress_candidate_from_active_inventory = _policy._suppress_candidate_from_active_inventory
_summary_for_legitimacy = _policy._summary_for_legitimacy


def build_inventory_snapshot(
    skills_root=None,
    candidate_root=None,
) -> dict[str, object]:
    return _builder.build_inventory_snapshot(
        sys.modules[__name__],
        skills_root=skills_root,
        candidate_root=candidate_root,
    )


def load_cached_inventory() -> dict[str, object]:
    return _builder.load_cached_inventory(sys.modules[__name__])


def _run_baselines(func, *args, **kwargs):
    original_root = _baselines.REPO_ROOT
    original_host_id = _baselines.host_id
    _baselines.REPO_ROOT = REPO_ROOT
    _baselines.host_id = host_id
    try:
        return func(*args, **kwargs)
    finally:
        _baselines.REPO_ROOT = original_root
        _baselines.host_id = original_host_id


def _iter_recent_work_radar_paths(*, limit: int = 2):
    return _run_baselines(_baselines._iter_recent_work_radar_paths, limit=limit)


def _fetch_github_dirs(repo: str, path: str = ""):
    return _run_baselines(_baselines._fetch_github_dirs, repo, path)


def fetch_openai_baseline():
    return _run_baselines(_baselines.fetch_openai_baseline)


def _load_vscode_codex_baseline_additions():
    return _run_baselines(_baselines._load_vscode_codex_baseline_additions)


def _parse_third_party_skill_attribution():
    return _run_baselines(_baselines._parse_third_party_skill_attribution)


def _parse_third_party_sources():
    return _run_baselines(_baselines._parse_third_party_sources)


def _parse_threat_matrix_sources():
    return _run_baselines(_baselines._parse_threat_matrix_sources)


def _parse_skillhub_source_ledger():
    return _run_baselines(_baselines._parse_skillhub_source_ledger)


def _recent_work_skill_names(candidate_root):
    return _run_baselines(_baselines._recent_work_skill_names, candidate_root)
