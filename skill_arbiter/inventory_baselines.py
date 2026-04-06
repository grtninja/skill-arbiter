from __future__ import annotations

import json
import re
from pathlib import Path
from urllib import error, request

from .contracts import SourceRecord
from .paths import REPO_ROOT, host_id

THIRD_PARTY_SOURCE_ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$")
THREAT_MATRIX_ROW_RE = re.compile(r"^\| `?([^|`]+?)`? \| `([^`]+)` \| ([^|]+) \| `([^`]+)` \| (.+?) \|$")
THIRD_PARTY_SKILL_ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$")
BASELINE_SKILL_BULLET_RE = re.compile(r"^\s*-\s*`?([a-z0-9._-]+)`?\s*$", re.IGNORECASE)
BASELINE_SECTION_HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$")

_RADAR_FIELD_PATHS = ("changed_files_sample", "dirty_files_sample", "skill_paths")
_RADAR_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9-]")
_PATH_SEGMENT_RE = re.compile(r"[\\/]")


def _iter_recent_work_radar_paths(*, limit: int = 2) -> list[Path]:
    refs = sorted((REPO_ROOT / "references").glob("cross_repo_open_work_radar_*.json"))
    return refs[-max(1, limit) :]


def _safe_load_radar_payload(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return payload if isinstance(payload, dict) else None
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _extract_tokens_from_path(path: str, candidate_names: set[str]) -> set[str]:
    found: set[str] = set()
    if not path:
        return found
    for segment in _PATH_SEGMENT_RE.split(path.replace(".", "/")):
        segment = segment.strip().lower()
        if not segment:
            continue
        if segment in candidate_names:
            found.add(segment)
        stem = segment.rsplit(".", 1)[0]
        if stem in candidate_names:
            found.add(stem)
    return found


def _extract_tokens_from_subject(subject: str, candidate_names: set[str]) -> set[str]:
    found: set[str] = set()
    for token in _RADAR_TOKEN_SPLIT_RE.split((subject or "").lower()):
        if token and token in candidate_names:
            found.add(token)
    return found


def _candidate_names_from_radar(payload: dict[str, object], candidate_names: set[str]) -> set[str]:
    found: set[str] = set()
    repos = payload.get("repos")
    if not isinstance(repos, list):
        return found
    for repo_entry in repos:
        if not isinstance(repo_entry, dict):
            continue
        for field in _RADAR_FIELD_PATHS:
            rows = repo_entry.get(field)
            if not isinstance(rows, list):
                continue
            for raw in rows:
                if not isinstance(raw, str):
                    continue
                found.update(_extract_tokens_from_path(raw, candidate_names))
        commits = repo_entry.get("commits_sample")
        if not isinstance(commits, list):
            continue
        for commit in commits:
            if not isinstance(commit, dict):
                continue
            found.update(_extract_tokens_from_subject(str(commit.get("subject") or ""), candidate_names))
    return found


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


def _load_vscode_codex_baseline_additions() -> tuple[set[str], set[str]]:
    path = REPO_ROOT / "references" / "vscode-codex-baseline-additions.md"
    if not path.is_file():
        return set(), set()
    additions: set[str] = set()
    system_additions: set[str] = set()
    section = "top_level"
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        heading_match = BASELINE_SECTION_HEADING_RE.match(line)
        if heading_match:
            heading = heading_match.group(1).strip().lower()
            section = "system" if "system" in heading else "top_level"
            continue
        match = BASELINE_SKILL_BULLET_RE.match(line)
        if match:
            target = system_additions if section == "system" else additions
            target.add(match.group(1).strip())
    return additions, system_additions


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


def _parse_skillhub_source_ledger() -> list[SourceRecord]:
    path = REPO_ROOT / "references" / "skillhub-source-ledger.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    current_host = host_id()
    first_wave_size = int(payload.get("first_wave_size") or 0)
    clean_pass_count = int(payload.get("clean_pass_count") or 0)
    manual_review_count = int(payload.get("manual_review_count") or 0)
    reject_count = int(payload.get("reject_count") or 0)
    notes = [
        f"source_status={payload.get('source_status') or 'unknown'}",
        f"first_wave_size={first_wave_size}",
        f"clean_pass_count={clean_pass_count}",
        f"manual_review_count={manual_review_count}",
        f"reject_count={reject_count}",
        f"promotion_decision={payload.get('promotion_decision') or 'unknown'}",
    ]
    return [
        SourceRecord(
            source_id=str(payload.get("source_id") or "skillhub"),
            source_type="marketplace_catalog",
            origin="skillhub",
            version_or_commit="phase1",
            local_presence="tracked_reference",
            drift_state="tracked",
            risk_class=str(payload.get("risk_class") or "medium"),
            recommended_action=str(payload.get("recommended_action") or "discovery_only"),
            host_id=current_host,
            remote_url=str(payload.get("remote_url") or "https://skills.palebluedot.live"),
            compatibility_surface=str(payload.get("compatibility_surface") or "marketplace_catalog"),
            notes=notes,
        )
    ]


def _candidate_names(candidate_root: Path) -> set[str]:
    if not candidate_root.is_dir():
        return set()
    return {item.name for item in candidate_root.iterdir() if item.is_dir()}


def _recent_work_skill_names(candidate_root: Path) -> set[str]:
    candidate_names = _candidate_names(candidate_root)
    if not candidate_names:
        return set()
    radar_paths = _iter_recent_work_radar_paths()
    radar_payloads: list[dict[str, object]] = []
    for path in radar_paths:
        payload = _safe_load_radar_payload(path)
        if payload is not None:
            radar_payloads.append(payload)
    if not radar_payloads:
        return set()
    detected = set()
    normalized_candidates = {name.lower() for name in candidate_names}
    for payload in radar_payloads:
        detected.update(_candidate_names_from_radar(payload, normalized_candidates))
    if detected:
        return detected
    radar_text = "\n".join(
        json.dumps(payload, ensure_ascii=True, sort_keys=True).lower() for payload in radar_payloads
    )
    return {
        name
        for name in candidate_names
        if str(name).lower() in radar_text
    }
