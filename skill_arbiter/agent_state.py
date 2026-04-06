from __future__ import annotations

import copy
import json
import threading
import time
from pathlib import Path
from typing import Any


class NullClawStateBase:
    def __init__(self, module, skills_root: Path | None = None, candidate_root: Path | None = None) -> None:
        self._module = module
        self.skills_root = skills_root or module.DEFAULT_SKILLS_ROOT
        self.candidate_root = candidate_root or module.DEFAULT_CANDIDATES_ROOT
        self.host_id = module.host_id()
        self._inventory_refresh_lock = threading.Lock()
        self._inventory_refresh_cache: dict[str, Any] = {
            "expires_at": 0.0,
            "payload": None,
        }

    def _candidate_root_label(self) -> str:
        try:
            return str(self.candidate_root.relative_to(self._module.REPO_ROOT))
        except ValueError:
            return "<external-candidate-root>"

    def ready(self) -> dict[str, object]:
        return {
            "status": "ok",
            "service": "nullclaw-agent",
            "application": "Skill Arbiter Security Console",
            "host_id": self.host_id,
        }

    def health(self) -> dict[str, object]:
        about = self._module.about_payload(self.host_id)
        advisor = self._module.advisor_status()
        collaboration_events = (
            self._module.read_collaboration_events(limit=200)
            if not about.get("stack_runtime_contract", {}).get("stack_health_url", "")
            else None
        )
        return {
            "status": "ok",
            "service": "nullclaw-agent",
            "application": about["application"],
            "version": about["version"],
            "host_id": self.host_id,
            "policy_mode": "guarded_auto",
            "skills_root": "$CODEX_HOME/skills",
            "candidate_root": self._candidate_root_label(),
            "inventory_ready": self._module.inventory_cache_path().is_file(),
            "self_checks_ready": self._module.self_check_cache_path().is_file(),
            "collaboration_ready": self._module.collaboration_log_path().is_file(),
            "quest_ready": self._module.quest_log_path().is_file(),
            "advisor_enabled": self._module.advisor_enabled(),
            "advisor_model": self._module.advisor_model(),
            "advisor_base_url": self._module.advisor_base_url(),
            "advisor_status": advisor["status"],
            "advisor_detail": advisor["detail"],
            "stack_mode": about.get("stack_runtime_contract", {}).get("stack_mode", ""),
            "stack_health_url": about.get("stack_runtime_contract", {}).get("stack_health_url", ""),
            "stack_runtime": self._module.stack_runtime_snapshot(fallback_events=collaboration_events),
            "poll_profile": self._module.load_poll_profile(),
        }

    def load_self_checks(self) -> dict[str, object]:
        path = self._module.self_check_cache_path()
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def run_self_checks(self) -> dict[str, object]:
        privacy = self._module.scan_repo(self._module.REPO_ROOT)
        governance = self._module.run_self_governance_scan(self._module.REPO_ROOT, privacy=privacy)
        payload = {
            "host_id": self.host_id,
            "privacy_passed": privacy.passed,
            "privacy_findings": [item.to_dict() for item in privacy.findings],
            "self_governance": governance,
        }
        self._module.self_check_cache_path().write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        self._module.append_audit_event(
            self._module.AuditEvent(
                event_type="self_checks_run",
                subject="repo",
                detail="ran privacy and self-governance checks",
                host_id=self.host_id,
                evidence_codes=[item.kind for item in privacy.findings[:6]],
            )
        )
        return payload

    def inventory_refresh(self, *, force: bool = False) -> dict[str, object]:
        now = time.time()
        if not force:
            with self._inventory_refresh_lock:
                cached = self._inventory_refresh_cache.get("payload")
                if self._inventory_refresh_cache["expires_at"] > now and cached is not None:
                    payload = copy.deepcopy(cached)
                    payload["refresh_cached"] = True
                    return payload
        payload = self._module.build_inventory_snapshot(self.skills_root, self.candidate_root)
        self._module.reconcile_cases(payload)
        payload["refresh_cached"] = False
        self._module.append_audit_event(
            self._module.AuditEvent(
                event_type="inventory_refresh",
                subject="skills",
                detail="refreshed local skill and source inventory",
                host_id=self.host_id,
                evidence_codes=[item["severity"] for item in payload.get("incidents", [])[:6]],
            )
        )
        with self._inventory_refresh_lock:
            self._inventory_refresh_cache["payload"] = payload
            self._inventory_refresh_cache["expires_at"] = now + max(
                10.0,
                self._module.load_poll_profile().get("passive_inventory_ms", 120000) / 1000.0,
            )
        return payload

    def public_readiness(self) -> dict[str, object]:
        payload = self._module.run_public_readiness_scan(self._module.REPO_ROOT)
        self._module.append_audit_event(
            self._module.AuditEvent(
                event_type="public_readiness_run",
                subject="repo",
                detail="evaluated public release readiness",
                host_id=self.host_id,
                evidence_codes=[item["code"] for item in payload.get("findings", [])[:6]],
            )
        )
        return payload

    def evaluate_skill(self, body: dict[str, object]) -> dict[str, object]:
        skill_name = str(body.get("skill_name") or "").strip()
        domain = str(body.get("domain") or "auto").strip()
        if not skill_name:
            raise ValueError("skill_name is required")
        candidates = [self.candidate_root / skill_name, self.skills_root / skill_name]
        target = None
        if domain == "candidate":
            target = self.candidate_root / skill_name
        elif domain == "installed":
            target = self.skills_root / skill_name
        else:
            for item in candidates:
                if item.is_dir():
                    target = item
                    break
        if target is None or not target.is_dir():
            raise FileNotFoundError(f"skill not found: {skill_name}")
        source_root = self.candidate_root if target.is_relative_to(self.candidate_root) else self.skills_root
        summary = self._module.summarize_findings(self._module.scan_skill_dir_content(target))["findings"] + self._module.summarize_findings(self._module.scan_skill_tree(target, source_root))["findings"]
        codes = list(dict.fromkeys(row["code"] for row in summary))
        severity = "low"
        if any(row["severity"] == "critical" for row in summary):
            severity = "critical"
        elif any(row["severity"] == "high" for row in summary):
            severity = "high"
        decision = self._module.PolicyDecision(
            subject=skill_name,
            action="quarantine" if severity in {"critical", "high"} else "keep",
            reason=f"evaluated {len(summary)} findings for skill",
            severity=severity,
            requires_confirmation=severity in {"critical", "high"},
            host_id=self.host_id,
            evidence_codes=codes,
        )
        self._module.append_audit_event(
            self._module.AuditEvent(
                event_type="admission_evaluate",
                subject=skill_name,
                detail=f"evaluated skill in {domain} domain",
                host_id=self.host_id,
                requires_confirmation=decision.requires_confirmation,
                evidence_codes=codes,
            )
        )
        return {"decision": decision.to_dict(), "findings": summary}
