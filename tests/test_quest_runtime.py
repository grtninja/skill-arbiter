from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skill_arbiter.quest_runtime import record_payload, status_payload


class QuestRuntimeTests(unittest.TestCase):
    def test_record_payload_requires_usable_outcome_for_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                record_payload(
                    inventory={"skills": []},
                    host_id="host-test",
                    request="stabilize meta-harness routing",
                    outcome="success",
                    skills_used=["skill-hub", "skill-enforcer"],
                    final_outcome="",
                    deliverables=[],
                    evidence=[],
                    dry_run=True,
                )

    def test_record_payload_persists_human_readable_quest_and_skill_awards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "quest-log.json"
            result = record_payload(
                inventory={"skills": [], "recent_work_skills": ["meta-harness-four-app-alignment"]},
                host_id="host-test",
                request="recover the full meta-harness stack",
                outcome="success",
                skills_used=["skill-hub", "local-compute-usage", "skill-enforcer"],
                required_skills=["skill-hub", "local-compute-usage", "skill-enforcer"],
                repo_scope=["skill-arbiter", "continue-meta-harness-private"],
                chain_id="meta-harness",
                title="Meta-Harness Recovery",
                final_outcome="All governed surfaces restored with authoritative routing intact.",
                deliverables=["updated runtime config", "validated control-plane snapshot"],
                evidence=["9000 authority check", "11420 bridge capability proof"],
                checkpoints=[
                    {"checkpoint_id": "authority", "label": "Authority pinned", "status": "done", "evidence": ["9000", "2337"]},
                    {"checkpoint_id": "bridge", "label": "Bridge healthy", "status": "done", "evidence": ["11420 capability report"]},
                ],
                steps=[
                    {"step_id": "route", "label": "Route the request", "status": "done", "skills": ["skill-hub"]},
                    {"step_id": "validate", "label": "Validate local stack", "status": "done", "skills": ["local-compute-usage"], "checkpoint_ids": ["authority", "bridge"]},
                    {"step_id": "close", "label": "Seal the policy lane", "status": "done", "skills": ["skill-enforcer"]},
                ],
                meta_harness=True,
                dry_run=True,
                path=log_path,
            )

        quest = result["quest"]
        self.assertEqual(quest["chain_id"], "meta-harness")
        self.assertTrue(quest["meta_harness"])
        self.assertEqual(quest["title"], "Meta-Harness Recovery")
        self.assertEqual(len(quest["steps"]), 3)
        self.assertEqual(len(quest["checkpoints"]), 2)
        self.assertGreater(len(quest["skill_xp_awards"]), 0)
        self.assertEqual(result["skill_game"]["agent_progression"]["level"], result["skill_game"]["level"])

    def test_status_payload_summarizes_top_questing_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "quest-log.json"
            inventory = {"skills": [], "recent_work_skills": ["meta-harness-four-app-alignment"]}
            record_payload(
                inventory=inventory,
                host_id="host-test",
                request="recover the meta-harness stack",
                outcome="success",
                skills_used=["skill-hub", "skill-enforcer"],
                chain_id="meta-harness",
                final_outcome="Recovered",
                deliverables=["runtime snapshot"],
                evidence=["health proof"],
                meta_harness=True,
                path=log_path,
            )
            record_payload(
                inventory=inventory,
                host_id="host-test",
                request="refresh candidate governance",
                outcome="partial",
                skills_used=["skill-hub"],
                chain_id="governance-core",
                final_outcome="",
                deliverables=[],
                evidence=[],
                path=log_path,
            )
            payload = status_payload(inventory, recent=5, path=log_path)

        self.assertEqual(payload["quest_count"], 2)
        self.assertEqual(payload["completed_count"], 1)
        self.assertEqual(payload["meta_harness_count"], 1)
        self.assertEqual(payload["top_skills"][0]["name"], "skill-hub")
        self.assertEqual(payload["active_chains"][0]["chain_id"], "governance-core")


if __name__ == "__main__":
    unittest.main()
