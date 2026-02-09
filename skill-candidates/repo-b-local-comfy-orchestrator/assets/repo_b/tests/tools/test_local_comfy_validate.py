from __future__ import annotations

from datetime import datetime, timezone
import sys
import unittest

from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import local_comfy_validate as validator  # noqa: E402


def _utc_iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


class LocalComfyValidateTests(unittest.TestCase):
    def _valid_payloads(self, now_epoch: float) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        status_payload = {
            "enabled": True,
            "reachable": True,
            "last_error": "",
            "checked_at": _utc_iso(now_epoch - 5),
        }
        queue_payload = {
            "running_prompt_ids": ["run-1"],
            "pending_prompt_ids": ["pend-1", "pend-2"],
            "running_count": 1,
            "pending_count": 2,
        }
        history_payload = {
            "entries": [
                {
                    "prompt_id": "pend-1",
                    "queue_state": "success",
                    "has_outputs": True,
                    "node_count": 3,
                },
                {
                    "prompt_id": "pend-2",
                    "queue_state": "running",
                    "has_outputs": False,
                    "node_count": 0,
                },
            ],
            "count": 2,
        }
        return status_payload, queue_payload, history_payload

    def test_strict_pass_when_all_resources_are_valid(self) -> None:
        now_epoch = 1_707_480_000.0
        status_payload, queue_payload, history_payload = self._valid_payloads(now_epoch)

        report = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=12,
            now_epoch=now_epoch,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["reason_codes"], [])
        self.assertTrue(report["checks"]["status_ok"])
        self.assertTrue(report["checks"]["queue_ok"])
        self.assertTrue(report["checks"]["history_ok"])
        self.assertLessEqual(report["hint_count"], 12)

    def test_fail_on_stale_or_unreachable_status(self) -> None:
        now_epoch = 1_707_480_000.0
        status_payload, queue_payload, history_payload = self._valid_payloads(now_epoch)
        status_payload["reachable"] = False
        status_payload["last_error"] = "connection refused"
        status_payload["checked_at"] = _utc_iso(now_epoch - 300)

        report = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=12,
            now_epoch=now_epoch,
        )

        self.assertEqual(report["status"], "validation_failed")
        self.assertIn("comfy_unreachable", report["reason_codes"])
        self.assertIn("stale_status", report["reason_codes"])

    def test_fail_on_queue_count_mismatch(self) -> None:
        now_epoch = 1_707_480_000.0
        status_payload, queue_payload, history_payload = self._valid_payloads(now_epoch)
        queue_payload["pending_count"] = 99

        report = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=12,
            now_epoch=now_epoch,
        )

        self.assertEqual(report["status"], "validation_failed")
        self.assertIn("schema_invalid", report["reason_codes"])

    def test_fail_on_malformed_history_rows(self) -> None:
        now_epoch = 1_707_480_000.0
        status_payload, queue_payload, history_payload = self._valid_payloads(now_epoch)
        history_payload["entries"] = [
            {
                "prompt_id": "pend-1",
                "queue_state": "success",
                "has_outputs": True,
                "node_count": "3",
            }
        ]
        history_payload["count"] = 1

        report = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=12,
            now_epoch=now_epoch,
        )

        self.assertEqual(report["status"], "validation_failed")
        self.assertIn("schema_invalid", report["reason_codes"])

    def test_hint_ranking_and_truncation_are_deterministic(self) -> None:
        now_epoch = 1_707_480_000.0
        status_payload = {
            "enabled": True,
            "reachable": False,
            "last_error": "offline",
            "checked_at": _utc_iso(now_epoch - 120),
        }
        queue_payload = {
            "running_prompt_ids": [],
            "pending_prompt_ids": [],
            "running_count": "0",
            "pending_count": "0",
        }
        history_payload = {
            "entries": [{"prompt_id": "bad-row"}],
            "count": 1,
        }

        report_a = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=2,
            now_epoch=now_epoch,
        )
        report_b = validator.validate_comfy_resources(
            status_payload=status_payload,
            queue_payload=queue_payload,
            history_payload=history_payload,
            status_max_age_seconds=60,
            max_hints=2,
            now_epoch=now_epoch,
        )

        self.assertEqual(report_a["guidance_hints"], report_b["guidance_hints"])
        self.assertEqual(report_a["hint_count"], 2)
        self.assertEqual(report_b["hint_count"], 2)


if __name__ == "__main__":
    unittest.main()
