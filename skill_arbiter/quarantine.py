from __future__ import annotations

import json
import os
import signal
import shutil
from pathlib import Path

from .audit_log import append_audit_event
from .contracts import AuditEvent, PolicyDecision
from .paths import DEFAULT_SKILLS_ROOT, host_id, quarantine_artifacts_root, quarantine_state_path


def _load_state() -> dict[str, object]:
    path = quarantine_state_path()
    if not path.is_file():
        return {"quarantined_skills": [], "blocked_paths": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(payload: dict[str, object]) -> None:
    path = quarantine_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def apply_quarantine(skill_name: str, skills_root: Path | None = None) -> PolicyDecision:
    root = skills_root or DEFAULT_SKILLS_ROOT
    blacklist = root / ".blacklist.local"
    live_skill_dir = root / skill_name
    quarantine_root = quarantine_artifacts_root() / "skills"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    quarantined_skill_dir = quarantine_root / skill_name
    root.mkdir(parents=True, exist_ok=True)
    names = set()
    if blacklist.is_file():
        names = {line.strip() for line in blacklist.read_text(encoding="utf-8").splitlines() if line.strip()}
    names.add(skill_name)
    blacklist.write_text("".join(f"{name}\n" for name in sorted(names)), encoding="utf-8")

    moved_path = ""
    if live_skill_dir.is_dir():
        if quarantined_skill_dir.exists():
            shutil.rmtree(quarantined_skill_dir, ignore_errors=True)
        shutil.move(str(live_skill_dir), str(quarantined_skill_dir))
        moved_path = str(quarantined_skill_dir)

    payload = _load_state()
    quarantined = set(payload.get("quarantined_skills", []))
    quarantined.add(skill_name)
    payload["quarantined_skills"] = sorted(quarantined)
    blocked_paths = {
        str(item).strip()
        for item in payload.get("blocked_paths", [])
        if str(item).strip()
    }
    if moved_path:
        blocked_paths.add(moved_path)
    payload["blocked_paths"] = sorted(blocked_paths)
    _save_state(payload)

    decision = PolicyDecision(
        subject=skill_name,
        action="quarantine_move" if moved_path else "quarantine",
        reason="skill moved out of the live skill root and added to local quarantine"
        if moved_path
        else "skill added to local quarantine and blacklist",
        severity="high",
        requires_confirmation=False,
        host_id=host_id(),
        evidence_codes=["local_blacklist", "local_quarantine_move"] if moved_path else ["local_blacklist"],
    )
    append_audit_event(
        AuditEvent(
            event_type="quarantine_apply",
            subject=skill_name,
            detail="moved skill out of the live root and added it to local quarantine and blacklist"
            if moved_path
            else "added skill to local quarantine and blacklist",
            host_id=host_id(),
            evidence_codes=["local_blacklist", "local_quarantine_move"] if moved_path else ["local_blacklist"],
        )
    )
    return decision


def release_quarantine(skill_name: str, skills_root: Path | None = None) -> PolicyDecision:
    root = skills_root or DEFAULT_SKILLS_ROOT
    blacklist = root / ".blacklist.local"
    live_skill_dir = root / skill_name
    quarantine_root = quarantine_artifacts_root() / "skills"
    quarantined_skill_dir = quarantine_root / skill_name
    if blacklist.is_file():
        names = [line.strip() for line in blacklist.read_text(encoding="utf-8").splitlines() if line.strip()]
        kept = [name for name in names if name != skill_name]
        if kept:
            blacklist.write_text("".join(f"{name}\n" for name in kept), encoding="utf-8")
        else:
            blacklist.unlink()

    restored = False
    if quarantined_skill_dir.is_dir() and (not live_skill_dir.exists()):
        shutil.move(str(quarantined_skill_dir), str(live_skill_dir))
        restored = True

    payload = _load_state()
    quarantined = [name for name in payload.get("quarantined_skills", []) if name != skill_name]
    payload["quarantined_skills"] = quarantined
    blocked_paths = [
        path for path in payload.get("blocked_paths", [])
        if str(path).strip() and str(path).strip() != str(quarantined_skill_dir)
    ]
    payload["blocked_paths"] = blocked_paths
    _save_state(payload)

    decision = PolicyDecision(
        subject=skill_name,
        action="restore_quarantine" if restored else "release_quarantine",
        reason="skill restored to the live root and removed from local quarantine after review"
        if restored
        else "skill removed from local quarantine after review",
        severity="medium",
        requires_confirmation=False,
        host_id=host_id(),
        evidence_codes=["local_blacklist_release", "local_quarantine_restore"] if restored else ["local_blacklist_release"],
    )
    append_audit_event(
        AuditEvent(
            event_type="quarantine_release",
            subject=skill_name,
            detail="restored skill to the live root and removed it from local quarantine and blacklist"
            if restored
            else "removed skill from local quarantine and blacklist",
            host_id=host_id(),
            evidence_codes=["local_blacklist_release", "local_quarantine_restore"] if restored else ["local_blacklist_release"],
        )
    )
    return decision


def confirm_delete_skill(skill_name: str, skills_root: Path | None = None) -> PolicyDecision:
    root = skills_root or DEFAULT_SKILLS_ROOT
    target = root / skill_name
    if target.is_dir():
        for child in sorted(target.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        target.rmdir()
    decision = PolicyDecision(
        subject=skill_name,
        action="delete_skill",
        reason="operator confirmed installed skill deletion",
        severity="high",
        requires_confirmation=False,
        host_id=host_id(),
        evidence_codes=["operator_confirmed_delete"],
    )
    append_audit_event(
        AuditEvent(
            event_type="delete_skill",
            subject=skill_name,
            detail="operator confirmed installed skill deletion",
            host_id=host_id(),
            evidence_codes=["operator_confirmed_delete"],
        )
    )
    return decision


def confirm_kill_process(pid: int) -> PolicyDecision:
    os.kill(pid, signal.SIGTERM)
    decision = PolicyDecision(
        subject=str(pid),
        action="kill_process",
        reason="operator confirmed process termination",
        severity="high",
        requires_confirmation=False,
        host_id=host_id(),
        evidence_codes=["operator_confirmed_kill"],
    )
    append_audit_event(
        AuditEvent(
            event_type="kill_process",
            subject=str(pid),
            detail="operator confirmed process termination",
            host_id=host_id(),
            evidence_codes=["operator_confirmed_kill"],
        )
    )
    return decision
