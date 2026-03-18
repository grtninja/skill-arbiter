from __future__ import annotations

import os
import unittest
from unittest import mock

from skill_arbiter import stack_runtime


class StackRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        stack_runtime._STACK_RUNTIME_CACHE["expires_at"] = 0.0
        stack_runtime._STACK_RUNTIME_CACHE["payload"] = None

    def test_load_poll_profile_reads_overrides(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SKILL_ARBITER_STACK_POLL_PROFILE": "full",
                "SKILL_ARBITER_STACK_HEALTH_MS": "15000",
                "SKILL_ARBITER_STACK_RUNTIME_MS": "4500",
            },
            clear=False,
        ):
            profile = stack_runtime.load_poll_profile()

        self.assertEqual(profile["name"], "full")
        self.assertEqual(profile["health_ms"], 15000)
        self.assertEqual(profile["stack_runtime_ms"], 10000)

    def test_stack_runtime_snapshot_falls_back_to_collaboration_events(self) -> None:
        events = [
            {
                "task": "stack_reconcile",
                "metadata": {
                    "mx3_mode": "media_assist",
                    "mx3_feeder_state": "active",
                    "mx3_owner_job_id": "job-42",
                    "mx3_active_sequence_name": "frame_qc_v1",
                    "mx3_active_dfp_path": "C:/temp/frame_qc_v1.dfp",
                },
            },
        ]
        with mock.patch.dict(os.environ, {"STARFRAME_STACK_HEALTH_URL": ""}, clear=False):
            payload = stack_runtime.stack_runtime_snapshot(fallback_events=events)

        self.assertFalse(payload["available"])
        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["mx3"]["mode"], "media_assist")
        self.assertEqual(payload["mx3"]["feeder_state"], "active")
        self.assertEqual(payload["mx3"]["owner_job_id"], "job-42")
        self.assertEqual(payload["mx3"]["active_sequence_name"], "frame_qc_v1")
        self.assertEqual(payload["mx3"]["active_dfp_path"], "frame_qc_v1.dfp")
        self.assertEqual(payload["subagent_coordination"]["source"], "collaboration_fallback")

    def test_stack_runtime_snapshot_caches_recent_health(self) -> None:
        with mock.patch.dict(os.environ, {"STARFRAME_STACK_HEALTH_URL": "http://127.0.0.1:12345/health"}, clear=False):
            with mock.patch("skill_arbiter.stack_runtime._fetch_stack_payload") as fetch:
                fetch.return_value = {
                    "status": "ok",
                    "telemetry": {"providers": {"lmstudio": {}, "mx3": {}}},
                    "mx3": {"mode": "media_assist"},
                }
                first = stack_runtime.stack_runtime_snapshot(force_refresh=True)
                second = stack_runtime.stack_runtime_snapshot()

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["mx3"]["mode"], "media_assist")
        self.assertEqual(first["providers"]["provider_count"], 2)
        self.assertFalse(first["providers"]["topology_exposed"])
        self.assertEqual(first["health"]["target"], "loopback")
        self.assertNotIn("payload", first["health"])
        self.assertEqual(second["status"], "ok")


if __name__ == "__main__":
    unittest.main()
