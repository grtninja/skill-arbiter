from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import QuestCheckpoint, QuestRecord, QuestStep, utc_now
from .paths import quest_log_path
from .skill_game_runtime import record_payload as record_skill_game_payload

VALID_OUTCOMES = {"success", "partial", "failed"}
VALID_STEP_STATUS = {"pending", "active", "done", "blocked", "failed", "skipped"}
VALID_CHECKPOINT_STATUS = {"pending", "done", "failed", "skipped"}


def _unique_names(values: list[object]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        name = str(value or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _load_log(path: Path | None = None) -> dict[str, Any]:
    target = path or quest_log_path()
    if not target.is_file():
        return {"version": 1, "updated_at": "", "quests": []}
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("quest log must be a JSON object")
    quests = payload.get("quests")
    if not isinstance(quests, list):
        payload["quests"] = []
    payload.setdefault("version", 1)
    payload.setdefault("updated_at", "")
    return payload


def _save_log(payload: dict[str, Any], path: Path | None = None) -> None:
    target = path or quest_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def read_quest_events(limit: int = 50, path: Path | None = None) -> list[dict[str, Any]]:
    payload = _load_log(path)
    quests = payload.get("quests")
    if not isinstance(quests, list):
        return []
    return quests[-max(0, limit) :]


def _normalize_checkpoints(rows: list[dict[str, Any]] | None) -> list[QuestCheckpoint]:
    checkpoints: list[QuestCheckpoint] = []
    seen: set[str] = set()
    for index, row in enumerate(rows or [], start=1):
        if not isinstance(row, dict):
            continue
        checkpoint_id = str(row.get("checkpoint_id") or row.get("id") or f"checkpoint-{index}").strip()
        if not checkpoint_id or checkpoint_id in seen:
            continue
        seen.add(checkpoint_id)
        status = str(row.get("status") or "done").strip().lower()
        if status not in VALID_CHECKPOINT_STATUS:
            raise ValueError(f"unsupported checkpoint status: {status}")
        checkpoints.append(
            QuestCheckpoint(
                checkpoint_id=checkpoint_id,
                label=str(row.get("label") or checkpoint_id.replace("-", " ")).strip(),
                status=status,
                summary=str(row.get("summary") or "").strip(),
                evidence=_unique_names(list(row.get("evidence") or [])),
            )
        )
    return checkpoints


def _normalize_steps(rows: list[dict[str, Any]] | None, skills_used: list[str], checkpoints: list[QuestCheckpoint]) -> list[QuestStep]:
    steps: list[QuestStep] = []
    checkpoint_ids = [item.checkpoint_id for item in checkpoints]
    seen: set[str] = set()
    for index, row in enumerate(rows or [], start=1):
        if not isinstance(row, dict):
            continue
        step_id = str(row.get("step_id") or row.get("id") or f"step-{index}").strip()
        if not step_id or step_id in seen:
            continue
        seen.add(step_id)
        status = str(row.get("status") or "done").strip().lower()
        if status not in VALID_STEP_STATUS:
            raise ValueError(f"unsupported quest step status: {status}")
        steps.append(
            QuestStep(
                step_id=step_id,
                label=str(row.get("label") or step_id.replace("-", " ")).strip(),
                status=status,
                skills=_unique_names(list(row.get("skills") or [])),
                summary=str(row.get("summary") or "").strip(),
                checkpoint_ids=_unique_names(list(row.get("checkpoint_ids") or [])),
            )
        )
    if steps:
        return steps
    if not skills_used:
        return [
            QuestStep(
                step_id="step-outcome",
                label="Produce usable outcome",
                status="done",
                skills=[],
                summary="Quest completed without explicit step breakdown.",
                checkpoint_ids=checkpoint_ids,
            )
        ]
    generated: list[QuestStep] = []
    for index, skill_name in enumerate(skills_used, start=1):
        generated.append(
            QuestStep(
                step_id=f"step-{index}",
                label=f"Run {skill_name}",
                status="done",
                skills=[skill_name],
                summary=f"{skill_name} contributed to the quest outcome.",
                checkpoint_ids=checkpoint_ids if index == len(skills_used) else [],
            )
        )
    return generated


def _validate_usable_outcome(outcome: str, final_outcome: str, deliverables: list[str], evidence: list[str]) -> None:
    if outcome != "success":
        return
    if not final_outcome.strip():
        raise ValueError("successful quests require final_outcome")
    if not deliverables:
        raise ValueError("successful quests require at least one deliverable")
    if not evidence:
        raise ValueError("successful quests require at least one evidence item")


def _skill_xp_awards(skills_used: list[str], checkpoints: list[QuestCheckpoint], steps: list[QuestStep], outcome: str) -> list[dict[str, Any]]:
    if not skills_used:
        return []
    done_checkpoints = sum(1 for item in checkpoints if item.status == "done")
    done_steps = sum(1 for item in steps if item.status == "done")
    base = 35 if outcome == "success" else 15 if outcome == "partial" else 5
    checkpoint_bonus = done_checkpoints * 10
    step_bonus = done_steps * 5
    total = base + checkpoint_bonus + step_bonus
    awards: list[dict[str, Any]] = []
    for index, skill_name in enumerate(skills_used):
        award = total
        if index == 0:
            award += 10
        awards.append(
            {
                "skill": skill_name,
                "xp": award,
                "reason": f"quest_completion:{outcome}",
            }
        )
    return awards


def status_payload(inventory: dict[str, object], recent: int = 5, path: Path | None = None) -> dict[str, Any]:
    quests = read_quest_events(limit=500, path=path)
    completed = [item for item in quests if str(item.get("outcome") or "") == "success"]
    meta_harness = [item for item in quests if bool(item.get("meta_harness"))]
    skill_xp: dict[str, int] = {}
    active_chains: dict[str, int] = {}
    for row in quests:
        chain_id = str(row.get("chain_id") or "").strip()
        if chain_id:
            active_chains[chain_id] = active_chains.get(chain_id, 0) + 1
        for award in row.get("skill_xp_awards", []) if isinstance(row.get("skill_xp_awards"), list) else []:
            if not isinstance(award, dict):
                continue
            skill_name = str(award.get("skill") or "").strip()
            xp = int(award.get("xp") or 0)
            if skill_name:
                skill_xp[skill_name] = skill_xp.get(skill_name, 0) + xp
    top_skills = [
        {"name": name, "quest_xp": xp}
        for name, xp in sorted(skill_xp.items(), key=lambda item: (-item[1], item[0]))[:6]
    ]
    active_chain_rows = [
        {"chain_id": chain_id, "quest_count": count}
        for chain_id, count in sorted(active_chains.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]
    return {
        "quest_count": len(quests),
        "completed_count": len(completed),
        "meta_harness_count": len(meta_harness),
        "completion_rate": round((len(completed) / len(quests)) * 100, 2) if quests else 0.0,
        "recent_quests": list(reversed(quests[-max(1, recent) :])),
        "top_skills": top_skills,
        "active_chains": active_chain_rows,
        "recommended_targets": inventory.get("recent_work_skills", []),
    }


def record_payload(
    *,
    inventory: dict[str, object],
    host_id: str,
    request: str,
    outcome: str,
    skills_used: list[str] | None = None,
    required_skills: list[str] | None = None,
    repo_scope: list[str] | None = None,
    checkpoints: list[dict[str, Any]] | None = None,
    steps: list[dict[str, Any]] | None = None,
    quest_id: str = "",
    chain_id: str = "",
    title: str = "",
    final_outcome: str = "",
    deliverables: list[str] | None = None,
    evidence: list[str] | None = None,
    meta_harness: bool = False,
    enforcer_pass: bool | None = None,
    dry_run: bool = False,
    path: Path | None = None,
) -> dict[str, Any]:
    request_text = str(request or "").strip()
    if not request_text:
        raise ValueError("request is required")
    normalized_outcome = str(outcome or "").strip().lower()
    if normalized_outcome not in VALID_OUTCOMES:
        raise ValueError(f"unsupported outcome: {outcome}")

    used = _unique_names(list(skills_used or []))
    required = _unique_names(list(required_skills or [])) or used
    repos = _unique_names(list(repo_scope or []))
    deliverable_rows = _unique_names(list(deliverables or []))
    evidence_rows = _unique_names(list(evidence or []))
    normalized_checkpoints = _normalize_checkpoints(checkpoints)
    normalized_steps = _normalize_steps(steps, used, normalized_checkpoints)
    _validate_usable_outcome(normalized_outcome, final_outcome, deliverable_rows, evidence_rows)
    quest_name = str(title or "").strip() or request_text[:80]
    normalized_chain = str(chain_id or "general").strip()
    if quest_id:
        normalized_quest_id = str(quest_id).strip()
    else:
        fingerprint = hashlib.sha1(
            json.dumps(
                {
                    "request": request_text,
                    "skills": used,
                    "outcome": normalized_outcome,
                    "chain_id": normalized_chain,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:12]
        normalized_quest_id = f"{normalized_chain}:{fingerprint}"
    awards = _skill_xp_awards(used, normalized_checkpoints, normalized_steps, normalized_outcome)

    quest = QuestRecord(
        quest_id=normalized_quest_id,
        chain_id=normalized_chain,
        title=quest_name,
        request=request_text,
        outcome=normalized_outcome,
        host_id=host_id,
        required_skills=required,
        skills_used=used,
        repo_scope=repos,
        meta_harness=bool(meta_harness),
        final_outcome=str(final_outcome or "").strip(),
        deliverables=deliverable_rows,
        evidence=evidence_rows,
        checkpoints=normalized_checkpoints,
        steps=normalized_steps,
        skill_xp_awards=awards,
    )
    quest_payload = quest.to_dict()

    log_payload = _load_log(path)
    quests = log_payload.setdefault("quests", [])
    if not isinstance(quests, list):
        raise ValueError("quest log quests must be a list")
    if not dry_run:
        quests.append(quest_payload)
        if len(quests) > 200:
            log_payload["quests"] = quests[-200:]
        log_payload["updated_at"] = utc_now()
        _save_log(log_payload, path)

    quest_bonus = min(250, sum(int(item.get("xp") or 0) for item in awards))
    skill_game = record_skill_game_payload(
        inventory=inventory,
        task=f"quest::{normalized_quest_id}",
        required_skills=required,
        used_skills=used,
        arbiter_report="",
        audit_report="",
        enforcer_pass=enforcer_pass if enforcer_pass is not None else (True if used else None),
        dry_run=dry_run,
        bonus_points=quest_bonus,
        bonus_label=f"quest:{normalized_chain}",
        context={
            "quest_id": normalized_quest_id,
            "chain_id": normalized_chain,
            "outcome": normalized_outcome,
            "meta_harness": bool(meta_harness),
            "checkpoint_count": len(normalized_checkpoints),
            "deliverable_count": len(deliverable_rows),
        },
    )
    status = status_payload(inventory, path=path)
    return {
        "quest": quest_payload,
        "quest_written": not dry_run,
        "skill_game": skill_game,
        **status,
    }
