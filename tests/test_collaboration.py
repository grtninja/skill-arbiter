from __future__ import annotations

import unittest
from unittest import mock

from skill_arbiter import collaboration


class CollaborationTests(unittest.TestCase):
    def setUp(self) -> None:
        collaboration._COLLAB_EVENTS_CACHE["events"] = None
        collaboration._COLLAB_EVENTS_CACHE["expires_at"] = 0.0

    def test_record_payload_uses_empty_audit_report_for_skill_game(self) -> None:
        inventory = {"skills": [], "skill_count": 0, "incident_count": 0}

        with mock.patch("skill_arbiter.collaboration._load_log", return_value={"version": 1, "updated_at": "now", "events": []}):
            with mock.patch("skill_arbiter.collaboration._save_log"):
                with mock.patch("skill_arbiter.collaboration._record_trust_events", return_value={"available": False, "records": []}):
                    with mock.patch("skill_arbiter.collaboration.status_payload", return_value={"event_count": 1, "recent_events": []}):
                        with mock.patch("skill_arbiter.collaboration.record_skill_game_payload", return_value={"xp_delta": 0, "clear_run": False}) as record_skill_game:
                            result = collaboration.record_payload(
                                inventory=inventory,
                                host_id="host-test",
                                task="stack_reconcile",
                                outcome="success",
                                skills_used=["skill-enforcer"],
                                proposed_skill_work=[{"name": "heterogeneous-stack-validation", "action": "upgrade"}],
                                note="validated stack",
                                stability="repeatable",
                            )

        self.assertTrue(result["event_written"])
        record_skill_game.assert_called_once()
        kwargs = record_skill_game.call_args.kwargs
        self.assertEqual(kwargs["arbiter_report"], "")
        self.assertEqual(kwargs["audit_report"], "")

    def test_status_payload_exposes_mx3_and_subagent_runtime(self) -> None:
        sample_log = {
            "version": 1,
            "updated_at": "2026-03-17T00:00:00Z",
            "events": [
                {
                    "task": "stack_reconcile",
                    "outcome": "success",
                    "metadata": {
                        "mx3_mode": "media_assist",
                        "mx3_feeder_state": "active",
                        "mx3_owner_job_id": "job-42",
                        "mx3_active_sequence_name": "frame_qc_v1",
                        "mx3_active_dfp_path": "C:/temp/dfp.json",
                    },
                    "collaborators": ["subagent-a", "skill-enforcer", "meshgpt-dcc"],
                    "stability": "stable",
                },
                {
                    "task": "stack_reconcile",
                    "outcome": "success",
                    "collaborators": ["subagent-a", "subagent-b"],
                    "proposed_skill_work": [
                        {"name": "skill-foo", "action": "upgrade", "score": 5, "reason": "runtime improvement"}
                    ],
                },
            ],
        }
        with mock.patch("skill_arbiter.collaboration._load_log", return_value=sample_log):
            result = collaboration.status_payload({"skills": []})

        mx3 = result["mx3_runtime"]
        subagents = result["subagent_coordination"]
        self.assertEqual(mx3["mode"], "media_assist")
        self.assertEqual(mx3["feeder_state"], "active")
        self.assertEqual(mx3["owner_job_id"], "job-42")
        self.assertEqual(mx3["active_sequence_name"], "frame_qc_v1")
        self.assertEqual(mx3["active_dfp_path"], "dfp.json")
        self.assertEqual(subagents["source"], "collaboration_fallback")
        self.assertEqual(subagents["observed_event_count"], 2)
        self.assertEqual(subagents["available"], True)
        active_names = {row["name"] for row in subagents["active_subagents"]}
        self.assertEqual(active_names, {"subagent-a", "subagent-b"})

    def test_status_payload_exposes_churn_metrics(self) -> None:
        sample_log = {
            "version": 1,
            "updated_at": "2026-03-17T00:00:00Z",
            "events": [
                {
                    "task": "subagent-loop-audit",
                    "outcome": "success",
                    "collaborators": ["subagent-a", "operator"],
                    "repo_scope": ["skill-arbiter"],
                    "stability": "stable",
                },
                {
                    "task": "subagent-loop-audit",
                    "outcome": "success",
                    "collaborators": ["subagent-a", "operator"],
                    "repo_scope": ["skill-arbiter"],
                    "stability": "stable",
                },
                {
                    "task": "subagent-loop-audit",
                    "outcome": "success",
                    "collaborators": ["subagent-a", "operator"],
                    "repo_scope": ["skill-arbiter"],
                    "stability": "stable",
                },
                {
                    "task": "subagent-loop-audit",
                    "outcome": "success",
                    "collaborators": ["subagent-b", "operator"],
                    "repo_scope": ["pc-control"],
                    "stability": "stable",
                },
                {
                    "task": "subagent-loop-audit",
                    "outcome": "success",
                    "collaborators": ["subagent-a", "operator"],
                    "repo_scope": ["skill-arbiter"],
                    "stability": "stable",
                },
            ],
        }
        with mock.patch("skill_arbiter.collaboration._load_log", return_value=sample_log):
            result = collaboration.status_payload({"skills": []})

        churn = result["churn"]
        self.assertTrue(churn["possible_review_loop"])
        self.assertEqual(churn["dominant_collaborator"], "subagent-a")
        self.assertEqual(churn["active_collaborator_count"], 2)
        self.assertGreater(churn["window_events"], 0)
        self.assertEqual(churn["scope_diversity"], 2)

    def test_record_payload_bounds_fields_and_subagent_admission(self) -> None:
        with mock.patch("skill_arbiter.collaboration._load_log", return_value={"version": 1, "events": []}):
            with mock.patch("skill_arbiter.collaboration._save_log"):
                with mock.patch("skill_arbiter.collaboration._record_trust_events", return_value={"available": False, "records": []}):
                    with mock.patch("skill_arbiter.collaboration.status_payload", return_value={"event_count": 1, "recent_events": []}):
                        with mock.patch("skill_arbiter.collaboration.record_skill_game_payload", return_value={"xp_delta": 0, "clear_run": False}):
                            with mock.patch.object(collaboration, "MAX_COLLABORATORS_PER_RECORD", 2), mock.patch.object(collaboration, "MAX_REPO_SCOPE_PER_RECORD", 1), mock.patch.object(collaboration, "MAX_PROPOSED_WORK_PER_RECORD", 1):
                                result = collaboration.record_payload(
                                    inventory={"skills": []},
                                    host_id="host-test",
                                    task="subagent-bounds",
                                    outcome="success",
                                    collaborators=["subagent-a", "subagent-b", "subagent-c", "subagent-d"],
                                    repo_scope=["skill-arbiter", "pc-control", "repo-b"],
                                    skills_used=["skill-a", "skill-b", "skill-c"],
                                    proposed_skill_work=[
                                        {"name": "skill-a", "action": "upgrade"},
                                        {"name": "skill-b", "action": "create"},
                                    ],
                                    note="bounded test",
                                )

        event = result["event"]
        self.assertEqual(event["collaborators"], ["subagent-a", "subagent-b"])
        self.assertEqual(event["repo_scope"], ["skill-arbiter"])
        self.assertEqual(event["skills_used"], ["skill-a"])
        self.assertEqual(event["proposed_skill_work"], [{"name": "skill-a", "action": "upgrade", "reason": "", "status": "suggested"}])
        self.assertIn("proposed_skill_work_trimmed", event["field_trims"])
        self.assertIn("collaborators_trimmed", event["field_trims"])
        self.assertIn("repo_scope_trimmed", event["field_trims"])
        self.assertIn("event", result)

    def test_status_payload_includes_candidate_intake_summary(self) -> None:
        inventory = {
            "recent_work_skills": ["candidate-keep", "candidate-block"],
            "skills": [
                {
                    "name": "candidate-keep",
                    "source_type": "overlay_candidate",
                    "origin": "skill_candidates",
                    "legitimacy_status": "third_party_trusted",
                    "recommended_action": "install_candidate",
                    "notes": ["recent_work_relevant"],
                },
                {
                    "name": "candidate-pending",
                    "source_type": "overlay_candidate",
                    "origin": "skill_candidates",
                    "legitimacy_status": "owned_review",
                    "recommended_action": "monitor",
                    "notes": [],
                },
                {
                    "name": "candidate-block",
                    "source_type": "overlay_candidate",
                    "origin": "skill_candidates",
                    "legitimacy_status": "blocked_hostile",
                    "recommended_action": "monitor",
                    "notes": ["recent_work_relevant"],
                },
            ],
        }
        with mock.patch("skill_arbiter.collaboration._load_log", return_value={"version": 1, "events": []}):
            result = collaboration.status_payload(inventory, recent=1)

        candidate_intake = result["candidate_intake"]
        self.assertEqual(candidate_intake["counts"]["admitted"], 1)
        self.assertEqual(candidate_intake["counts"]["pending"], 0)
        self.assertEqual(candidate_intake["counts"]["rejected"], 1)
        names = {row["name"]: row["decision"] for row in candidate_intake["candidates"]}
        self.assertEqual(names["candidate-keep"], "admitted")
        self.assertEqual(names["candidate-block"], "rejected")

    def test_status_payload_subagent_admission_triggers_stagger_hint(self) -> None:
        sample_log = {
            "version": 1,
            "updated_at": "2026-03-17T00:00:00Z",
            "events": [
                {
                    "task": "render-review",
                    "outcome": "success",
                    "collaborators": ["faraday", "operator"],
                },
                {
                    "task": "render-review",
                    "outcome": "success",
                    "collaborators": ["faraday", "operator"],
                },
                {
                    "task": "render-review",
                    "outcome": "success",
                    "collaborators": ["faraday", "operator"],
                },
            ],
        }
        with mock.patch("skill_arbiter.collaboration._load_log", return_value=sample_log):
            result = collaboration.status_payload({"skills": []})

        subagent_admission = result["subagent_admission"]
        self.assertEqual(subagent_admission["mode"], "bounded")
        self.assertIn("stagger_task_loop:render-review", subagent_admission["recommendations"])
        active = {row["name"] for row in subagent_admission["active_subagents"]}
        self.assertIn("faraday", active)


if __name__ == "__main__":
    unittest.main()
