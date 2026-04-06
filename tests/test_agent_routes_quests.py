from __future__ import annotations

import unittest
from http import HTTPStatus
from types import SimpleNamespace

from skill_arbiter.agent_routes import handle_get, handle_post


class AgentRoutesQuestTests(unittest.TestCase):
    def test_handle_get_returns_quest_status(self) -> None:
        module = SimpleNamespace(
            load_cached_inventory=lambda: {"skills": []},
            quest_status_payload=lambda inventory: {"quest_count": 4, "completed_count": 3},
        )
        state = SimpleNamespace(host_id="host-test")

        status, payload = handle_get(module, state, "/v1/quests/status")

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["host_id"], "host-test")
        self.assertEqual(payload["quest_count"], 4)

    def test_handle_post_records_quest(self) -> None:
        audit_events: list[object] = []

        class FakeAuditEvent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        module = SimpleNamespace(
            load_cached_inventory=lambda: {"skills": []},
            record_quest_payload=lambda **kwargs: {
                "quest": {
                    "quest_id": "meta-harness:demo123",
                    "skill_xp_awards": [{"skill": "skill-hub", "xp": 90}],
                },
                "quest_written": True,
            },
            append_audit_event=lambda event: audit_events.append(event),
            AuditEvent=FakeAuditEvent,
        )
        state = SimpleNamespace(host_id="host-test")

        status, payload = handle_post(
            module,
            state,
            "/v1/quests/record",
            {
                "request": "recover the meta-harness stack",
                "outcome": "success",
                "skills_used": ["skill-hub"],
                "final_outcome": "Recovered",
                "deliverables": ["snapshot"],
                "evidence": ["health proof"],
            },
        )

        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["quest_written"])
        self.assertEqual(payload["quest"]["quest_id"], "meta-harness:demo123")
        self.assertEqual(len(audit_events), 1)
        self.assertEqual(audit_events[0].kwargs["event_type"], "quest_record")


if __name__ == "__main__":
    unittest.main()
