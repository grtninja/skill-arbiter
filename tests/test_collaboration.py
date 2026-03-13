from __future__ import annotations

import unittest
from unittest import mock

from skill_arbiter import collaboration


class CollaborationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
