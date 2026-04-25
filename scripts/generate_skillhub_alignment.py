#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.inventory import build_inventory_snapshot
from skill_arbiter.paths import REPO_ROOT


USER_AGENT = "Mozilla/5.0 SkillArbiterSkillHubPhase1/1.0"
SKILLHUB_BASE = "https://skills.palebluedot.live/api/skills"
QUERY_PACK = ["review", "audit", "skills", "workflow", "debug", "trace", "monitor", "browser"]
FIRST_WAVE = [
    {
        "name": "find-skills",
        "github_owner": "vercel-labs",
        "github_repo": "skills",
        "mode": "direct_vet",
        "mapping": "direct support for SkillHub monitoring and future marketplace sync",
        "target_gap": "skillhub-marketplace-sync",
        "decision_hint": "import_candidate",
    },
    {
        "name": "trending-skills",
        "github_owner": "openclaw",
        "github_repo": "skills",
        "mode": "direct_vet",
        "mapping": "direct support for SkillHub monitoring and future marketplace sync",
        "target_gap": "skillhub-marketplace-sync",
        "decision_hint": "import_candidate",
    },
    {
        "name": "trending-skills-monitor",
        "github_owner": "openclaw",
        "github_repo": "skills",
        "mode": "direct_vet",
        "mapping": "direct support for SkillHub monitoring and future marketplace sync",
        "target_gap": "skillhub-marketplace-sync",
        "decision_hint": "import_candidate",
    },
    {
        "name": "topic-monitor",
        "github_owner": "openclaw",
        "github_repo": "skills",
        "mode": "direct_vet",
        "mapping": "future operator monitoring lane if source and schedule posture are clean",
        "target_gap": "shockwave-dashboard-ops",
        "decision_hint": "import_candidate",
    },
    {
        "name": "review-pr",
        "github_owner": "openclaw",
        "github_repo": "openclaw",
        "mode": "direct_vet",
        "mapping": "overlap check against gh-address-comments / gh-fix-ci",
        "target_gap": "media-workbench-worker-contracts",
        "decision_hint": "ignore_overlap",
    },
    {
        "name": "agent-tracing",
        "github_owner": "lobehub",
        "github_repo": "lobehub",
        "mode": "direct_vet",
        "mapping": "possible import or partial rewrite for media-workbench-worker-contracts and avatarcore-runtime-handoff-ops",
        "target_gap": "media-workbench-worker-contracts",
        "decision_hint": "import_candidate",
    },
    {
        "name": "workflow-orchestration-patterns",
        "github_owner": "wshobson",
        "github_repo": "agents",
        "mode": "direct_vet",
        "mapping": "rewrite inspiration for shockwave-operator-handoff and qwen-training-campaign-ops",
        "target_gap": "shockwave-operator-handoff",
        "decision_hint": "rewrite_candidate",
    },
    {
        "name": "agentic-eval",
        "github_owner": "github",
        "github_repo": "awesome-copilot",
        "mode": "direct_vet",
        "mapping": "rewrite inspiration for qwen-training-checkpoint-eval expansion and future dataset/campaign lanes",
        "target_gap": "qwen-training-dataset-factory",
        "decision_hint": "rewrite_candidate",
    },
    {
        "name": "project-management-skills",
        "github_owner": "openclaw",
        "github_repo": "skills",
        "mode": "rewrite_only",
        "mapping": "rewrite-only inspiration for operator handoff and campaign lanes",
        "target_gap": "qwen-training-campaign-ops",
        "decision_hint": "rewrite_candidate",
    },
    {
        "name": "debugging-strategies",
        "github_owner": "wshobson",
        "github_repo": "agents",
        "mode": "rewrite_only",
        "mapping": "rewrite-only inspiration for worker contracts and startup acceptance lanes",
        "target_gap": "avatarcore-desktop-acceptance",
        "decision_hint": "rewrite_candidate",
    },
    {
        "name": "monitoring-expert",
        "github_owner": "Jeffallan",
        "github_repo": "claude-skills",
        "mode": "rewrite_only",
        "mapping": "rewrite-only inspiration for dashboard/operator monitoring lanes",
        "target_gap": "media-workbench-indexing-governance",
        "decision_hint": "rewrite_candidate",
    },
]


@dataclass(frozen=True)
class SkillHubSelection:
    name: str
    github_owner: str
    github_repo: str
    mode: str
    mapping: str
    target_gap: str
    decision_hint: str

    @property
    def skillhub_id(self) -> str:
        return f"{self.github_owner}/{self.github_repo}/{self.name}"


def _request_json(url: str) -> dict[str, Any]:
    req = request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _search_skillhub(query: str, limit: int = 30) -> dict[str, Any]:
    return _request_json(f"{SKILLHUB_BASE}?q={query}&limit={limit}")


def _fetch_skillhub_detail(selection: SkillHubSelection) -> dict[str, Any]:
    return _request_json(f"{SKILLHUB_BASE}/{selection.github_owner}/{selection.github_repo}/{selection.name}")


def _download_bytes(url: str) -> bytes:
    req = request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with request.urlopen(req, timeout=30) as response:
        return response.read()


def _fetch_github_contents(owner: str, repo: str, path: str, ref: str) -> Any:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path.strip('/')}?ref={ref}"
    return json.loads(_download_bytes(api_url).decode("utf-8"))


def _materialize_contents_tree(*, owner: str, repo: str, ref: str, remote_path: str, local_root: Path) -> int:
    payload = _fetch_github_contents(owner, repo, remote_path, ref)
    if isinstance(payload, dict) and payload.get("type") == "file":
        target = local_root / Path(remote_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_download_bytes(str(payload.get("download_url") or "")))
        return 1
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected GitHub contents payload for {owner}/{repo}:{remote_path}")
    count = 0
    for item in payload:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        item_path = str(item.get("path") or "")
        if not item_path:
            continue
        if item_type == "dir":
            count += _materialize_contents_tree(owner=owner, repo=repo, ref=ref, remote_path=item_path, local_root=local_root)
        elif item_type == "file":
            target = local_root / Path(item_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_download_bytes(str(item.get("download_url") or "")))
            count += 1
    return count


def _fetch_repo_subtree(workdir: Path, selection: SkillHubSelection, detail: dict[str, Any]) -> Path:
    branch = str(detail.get("branch") or "main").strip() or "main"
    skill_path = str(detail.get("skillPath") or "").strip().replace("\\", "/").strip("/")
    if not skill_path:
        raise RuntimeError(f"SkillHub detail for {selection.skillhub_id} is missing skillPath")
    base = workdir / f"{selection.github_owner}-{selection.github_repo}-{selection.name}"
    source_dir = base / Path(skill_path)
    matched = _materialize_contents_tree(
        owner=selection.github_owner,
        repo=selection.github_repo,
        ref=branch,
        remote_path=skill_path,
        local_root=base,
    )
    if matched == 0 or not source_dir.is_dir():
        raise FileNotFoundError(f"Fetched path missing for {selection.skillhub_id}: {source_dir}")
    return source_dir


def _write_attribution(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Third-Party Skill Attribution",
        "",
        "| `local_skill` | `origin_skill` | `source_label` | `intake_recommendation` | `origin_path` |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| `{local_skill}` | `{origin_skill}` | `{source_label}` | `{intake_recommendation}` | `{origin_path}` |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_json_command(command: list[str], cwd: Path) -> Any:
    subprocess.run(command, cwd=str(cwd), check=True, capture_output=True, text=True)
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_public_shape(value: Any, *, temp_root: Path | None = None) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_public_shape(item, temp_root=temp_root) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_public_shape(item, temp_root=temp_root) for item in value]
    if isinstance(value, str):
        text = value
        if temp_root:
            text = text.replace(str(temp_root), "<temp-skillhub-root>")
        text = text.replace(str(Path.home()), "$HOME")
        text = text.replace(str(REPO_ROOT), "<repo-root>")
        return text
    return value


def _current_inventory_names() -> set[str]:
    payload = build_inventory_snapshot()
    return {str(row.get("name") or "").strip().lower() for row in payload.get("skills", []) if str(row.get("name") or "").strip()}


def _score_decision(selection: SkillHubSelection, intake_row: dict[str, Any] | None, arbiter_row: dict[str, Any] | None, current_names: set[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if selection.name.lower() in current_names:
        return "ignore_overlap", ["already covered by current local inventory name match"]
    if selection.mode == "rewrite_only":
        return "rewrite_candidate", ["explicit rewrite-only inspiration lane"]
    if selection.decision_hint == "ignore_overlap":
        return "ignore_overlap", [selection.mapping]
    if intake_row:
        rec = str(intake_row.get("recommendation") or "").strip().lower()
        blockers = int(intake_row.get("blocker_count") or 0)
        if rec == "reject" or blockers > 0:
            reasons.append("third-party intake found blockers")
            return "rewrite_candidate", reasons
    if arbiter_row:
        action = str(arbiter_row.get("action") or "").strip().lower()
        if action == "remove" or bool(arbiter_row.get("supply_chain_blocked")):
            reasons.append("lockdown admission blocked direct import")
            return "rewrite_candidate", reasons
    reasons.append(selection.mapping)
    return selection.decision_hint, reasons


def _render_matrix(rows: list[dict[str, Any]], ledger: dict[str, Any]) -> str:
    lines = [
        "# SkillHub Alignment Matrix",
        "",
        "This document is machine-generated by `scripts/generate_skillhub_alignment.py` from the bounded SkillHub Phase 1 intake workflow.",
        "",
        "## Source Reputation",
        "",
        f"- Source status: `{ledger['source_status']}`",
        f"- First wave size: `{ledger['first_wave_size']}`",
        f"- Clean pass count: `{ledger['clean_pass_count']}`",
        f"- Manual review count: `{ledger['manual_review_count']}`",
        f"- Reject count: `{ledger['reject_count']}`",
        f"- Promotion decision: `{ledger['promotion_decision']}`",
        "",
        "## First-Wave Matrix",
        "",
        "| Skill | Repo | Mode | SkillHub metadata | Current coverage | Decision | Intake | Lockdown | Destination lane | Security blockers |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        metadata = f"score={row['securityScore']}; review={row['reviewStatus']}; downloads={row['downloadCount']}; stars={row['githubStars']}"
        blockers = ", ".join(row["security_blockers"]) if row["security_blockers"] else "-"
        lines.append(
            "| `{name}` | `{repo}` | `{mode}` | {metadata} | {coverage} | `{decision}` | `{intake}` | `{lockdown}` | `{lane}` | {blockers} |".format(
                name=row["name"],
                repo=f"{row['githubOwner']}/{row['githubRepo']}",
                mode=row["mode"],
                metadata=metadata,
                coverage=row["current_coverage"],
                decision=row["decision"],
                intake=row["intake_recommendation"],
                lockdown=row["lockdown_action"],
                lane=row["destination_lane"],
                blockers=blockers,
            )
        )
    return "\n".join(lines) + "\n"


def _render_ledger_md(ledger: dict[str, Any]) -> str:
    lines = [
        "# SkillHub Source Ledger",
        "",
        "SkillHub stays a discovery-first source until bounded first-wave intake, lockdown admission, and practical usefulness review support promotion.",
        "",
        f"- Source status: `{ledger['source_status']}`",
        f"- API base: `{ledger['api_base']}`",
        f"- Query set: `{', '.join(ledger['query_pack'])}`",
        f"- First wave size: `{ledger['first_wave_size']}`",
        f"- Clean pass count: `{ledger['clean_pass_count']}`",
        f"- Manual review count: `{ledger['manual_review_count']}`",
        f"- Reject count: `{ledger['reject_count']}`",
        f"- Promotion decision: `{ledger['promotion_decision']}`",
        f"- Promotion rationale: {ledger['promotion_rationale']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    current_names = _current_inventory_names()
    selections = [SkillHubSelection(**item) for item in FIRST_WAVE]
    evidence_dir = REPO_ROOT / "evidence"
    references_dir = REPO_ROOT / "references"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    references_dir.mkdir(parents=True, exist_ok=True)

    discovery_payload: dict[str, Any] = {"queries": {}, "shortlist": [], "fetched_at": None}
    for query in QUERY_PACK:
        payload = _search_skillhub(query, limit=30)
        discovery_payload["queries"][query] = payload
    discovery_payload["shortlist"] = [selection.skillhub_id for selection in selections]

    rows: list[dict[str, Any]] = []
    intake_json: dict[str, Any] = {"skills": []}
    arbiter_json: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="skillhub-phase1-") as tmp:
        temp_root = Path(tmp)
        source_root = temp_root / "source-root"
        refs_root = temp_root / "references"
        dest_root = temp_root / "dest"
        source_root.mkdir(parents=True, exist_ok=True)
        refs_root.mkdir(parents=True, exist_ok=True)
        dest_root.mkdir(parents=True, exist_ok=True)

        attribution_rows: list[dict[str, str]] = []
        detail_by_name: dict[str, dict[str, Any]] = {}
        fetch_failures: dict[str, str] = {}

        for selection in selections:
            detail = _fetch_skillhub_detail(selection)
            detail_by_name[selection.name] = detail
            try:
                cloned_path = _fetch_repo_subtree(temp_root, selection, detail)
                target_dir = source_root / selection.name
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(cloned_path, target_dir)
                attribution_rows.append(
                    {
                        "local_skill": selection.name,
                        "origin_skill": selection.name,
                        "source_label": "skillhub",
                        "intake_recommendation": "pending",
                        "origin_path": f"https://github.com/{selection.github_owner}/{selection.github_repo}/tree/{detail.get('branch') or 'main'}/{str(detail.get('skillPath') or '').strip('/')}",
                    }
                )
            except Exception as exc:
                fetch_failures[selection.name] = f"{exc.__class__.__name__}: {exc}"

        _write_attribution(refs_root / "third-party-skill-attribution.md", attribution_rows)

        intake_output = temp_root / "skillhub-intake.json"
        if any(source_root.iterdir()):
            subprocess.run(
                [
                    sys.executable,
                    str(Path.home() / ".codex" / "skills" / "skills-third-party-intake" / "scripts" / "third_party_skill_intake.py"),
                    "--source-root",
                    f"skillhub={source_root}",
                    "--json-out",
                    str(intake_output),
                ],
                cwd=str(REPO_ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            intake_json = _load_json(intake_output)
        intake_rows = {str(row.get("skill") or ""): row for row in intake_json.get("skills", [])}

        admitted = [
            selection.name
            for selection in selections
            if selection.mode == "direct_vet"
            and str(intake_rows.get(selection.name, {}).get("recommendation") or "").strip().lower() == "admit"
        ]
        arbiter_rows: dict[str, dict[str, Any]] = {}
        if admitted:
            arbiter_output = temp_root / "skillhub-arbiter.json"
            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "arbitrate_skills.py"),
                    *admitted,
                    "--source-dir",
                    str(source_root),
                    "--dest",
                    str(dest_root),
                    "--personal-lockdown",
                    "--json-out",
                    str(arbiter_output),
                ],
                cwd=str(REPO_ROOT),
                check=True,
                capture_output=True,
                text=True,
            )
            arbiter_json = _load_json(arbiter_output)
            arbiter_result_rows = arbiter_json.get("results", []) if isinstance(arbiter_json, dict) else arbiter_json
            arbiter_rows = {
                str(row.get("skill") or ""): row
                for row in arbiter_result_rows
                if isinstance(row, dict)
            }

        for selection in selections:
            detail = detail_by_name[selection.name]
            fetch_error = fetch_failures.get(selection.name, "")
            intake_row = intake_rows.get(selection.name)
            arbiter_row = arbiter_rows.get(selection.name)
            decision, decision_reasons = _score_decision(selection, intake_row, arbiter_row, current_names)
            security_blockers: list[str] = []
            if fetch_error:
                security_blockers.append(f"fetch_error:{fetch_error}")
                decision = "ignore_overlap" if selection.mode == "direct_vet" else "rewrite_candidate"
                decision_reasons = ["GitHub source resolution failed; deny direct intake until metadata/source mismatch is understood."]
            if intake_row:
                security_blockers.extend(list(intake_row.get("high_risk_hits") or []))
                security_blockers.extend(list(intake_row.get("unsafe_links") or []))
            if arbiter_row:
                security_blockers.extend(list(arbiter_row.get("supply_chain_codes") or []))
            security_blockers = list(dict.fromkeys(str(item) for item in security_blockers if str(item).strip()))
            current_coverage = "uncovered"
            if selection.name.lower() in current_names:
                current_coverage = "exact local skill already present"
            elif decision == "ignore_overlap":
                current_coverage = "functional overlap with current local inventory"
            elif decision == "rewrite_candidate":
                current_coverage = "needs repo-owned rewrite before safe alignment"
            rows.append(
                {
                    "skillhub_id": detail.get("id") or selection.skillhub_id,
                    "name": selection.name,
                    "githubOwner": selection.github_owner,
                    "githubRepo": selection.github_repo,
                    "mode": selection.mode,
                    "skillPath": detail.get("skillPath") or "",
                    "branch": detail.get("branch") or "",
                    "securityScore": int(detail.get("securityScore") or 0),
                    "securityStatus": detail.get("securityStatus") or "",
                    "downloadCount": int(detail.get("downloadCount") or 0),
                    "githubStars": int(detail.get("githubStars") or 0),
                    "reviewStatus": detail.get("reviewStatus") or "",
                    "query_origin": ",".join(sorted(query for query, payload in discovery_payload["queries"].items() if any(str(item.get("id") or "") == (detail.get("id") or selection.skillhub_id) for item in payload.get("skills", [])))),
                    "current_coverage": current_coverage,
                    "decision": decision,
                    "decision_reason": "; ".join(decision_reasons),
                    "fetch_error": fetch_error,
                    "intake_recommendation": str(intake_row.get("recommendation") or "not_scanned") if intake_row else "not_scanned",
                    "intake_blockers": int(intake_row.get("blocker_count") or 0) if intake_row else 0,
                    "lockdown_action": str(arbiter_row.get("action") or "not_run") if arbiter_row else "not_run",
                    "lockdown_supply_chain_blocked": bool(arbiter_row.get("supply_chain_blocked")) if arbiter_row else False,
                    "destination_lane": selection.target_gap,
                    "ownership_target": "repo_owned_rewrite" if decision == "rewrite_candidate" else "third_party_candidate",
                    "mapping": selection.mapping,
                    "security_blockers": security_blockers,
                }
            )

    clean_pass_count = sum(
        1
        for row in rows
        if row["decision"] == "import_candidate"
        and row["intake_recommendation"] == "admit"
        and row["lockdown_action"] in {"allow", "keep"}
        and not row["security_blockers"]
    )
    manual_review_count = sum(1 for row in rows if row["decision"] == "rewrite_candidate")
    reject_count = sum(1 for row in rows if row["decision"] == "ignore_overlap" or row["intake_recommendation"] == "reject")
    promotion_decision = "discovery_only"
    promotion_rationale = (
        "SkillHub remains discovery_only until the first wave proves stable through third-party intake, "
        "lockdown admission, and practical usefulness review."
    )
    if clean_pass_count >= max(1, len(rows) // 2) and reject_count == 0:
        promotion_decision = "relatively_reputable"
        promotion_rationale = "At least half of the first wave admitted cleanly with no critical mismatch between marketplace metadata and fetched source."

    ledger = {
        "source_id": "skillhub",
        "source_status": "discovery_only",
        "api_base": SKILLHUB_BASE,
        "remote_url": "https://skills.palebluedot.live",
        "query_pack": QUERY_PACK,
        "first_wave_size": len(rows),
        "clean_pass_count": clean_pass_count,
        "manual_review_count": manual_review_count,
        "reject_count": reject_count,
        "promotion_decision": promotion_decision,
        "promotion_rationale": promotion_rationale,
        "risk_class": "medium" if promotion_decision == "discovery_only" else "monitor",
        "recommended_action": "discovery_only" if promotion_decision == "discovery_only" else "bounded_promote",
        "compatibility_surface": "marketplace_catalog",
    }

    evidence_payload = {
        "discovery": discovery_payload,
        "first_wave": rows,
        "ledger": ledger,
        "intake": _sanitize_public_shape(intake_json, temp_root=temp_root),
        "arbiter": _sanitize_public_shape(arbiter_json, temp_root=temp_root),
    }
    evidence_payload = _sanitize_public_shape(evidence_payload, temp_root=temp_root)
    (evidence_dir / "skillhub_alignment_phase1.json").write_text(json.dumps(evidence_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (references_dir / "skillhub-source-ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (references_dir / "skillhub-source-ledger.md").write_text(_render_ledger_md(ledger), encoding="utf-8")
    (references_dir / "skillhub-alignment-matrix.md").write_text(_render_matrix(rows, ledger), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
