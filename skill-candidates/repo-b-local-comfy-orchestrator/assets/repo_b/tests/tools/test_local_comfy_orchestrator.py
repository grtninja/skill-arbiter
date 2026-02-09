from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import local_comfy_orchestrator as orchestrator  # noqa: E402


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LocalComfyOrchestratorTests(unittest.TestCase):
    def _args(self, repo_root: Path) -> argparse.Namespace:
        return argparse.Namespace(
            task="comfy-task-1",
            json_out=str(repo_root / "out.json"),
            repo_root=str(repo_root),
            base_url="http://127.0.0.1:9000",
            timeout_seconds=0.5,
        )

    def _env(self) -> dict[str, str]:
        return {
            "REPO_B_LOCAL_COMFY_ORCH_ENABLED": "1",
            "REPO_B_LOCAL_COMFY_ORCH_FAIL_CLOSED": "1",
            "REPO_B_LOCAL_COMFY_ORCH_STATUS_MAX_AGE_SECONDS": "60",
            "REPO_B_LOCAL_COMFY_ORCH_MAX_HINTS": "12",
        }

    def _mcp_status_payload(self, host: str = "127.0.0.1") -> dict[str, object]:
        return {
            "enabled": True,
            "running": True,
            "host": host,
            "port": 9550,
            "comfy": {
                "enabled": True,
                "reachable": True,
                "checked_at": _utc_now_iso(),
                "last_error": "",
            },
        }

    def _resource_probe_payload(self) -> dict[str, object]:
        return {
            "ok": True,
            "initialize_ok": True,
            "resources_list_ok": True,
            "available_resources": [
                "shim.comfy.status",
                "shim.comfy.queue",
                "shim.comfy.history",
            ],
            "reads": {
                "shim.comfy.status": {
                    "ok": True,
                    "error": "",
                    "payload": {
                        "enabled": True,
                        "reachable": True,
                        "checked_at": _utc_now_iso(),
                        "last_error": "",
                    },
                },
                "shim.comfy.queue": {
                    "ok": True,
                    "error": "",
                    "payload": {
                        "running_prompt_ids": ["run-1"],
                        "pending_prompt_ids": ["pend-1"],
                        "running_count": 1,
                        "pending_count": 1,
                    },
                },
                "shim.comfy.history": {
                    "ok": True,
                    "error": "",
                    "payload": {
                        "entries": [
                            {
                                "prompt_id": "pend-1",
                                "queue_state": "success",
                                "has_outputs": True,
                                "node_count": 1,
                            }
                        ],
                        "count": 1,
                    },
                },
            },
            "error": "",
        }

    def test_policy_violation_when_mcp_host_is_non_loopback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            args = self._args(repo_root)

            with mock.patch.object(
                orchestrator,
                "get_mcp_status",
                return_value={"ok": True, "status": 200, "payload": self._mcp_status_payload(host="192.168.1.55"), "error": ""},
            ):
                code, payload = orchestrator.run(args, environ=self._env())

            self.assertEqual(code, orchestrator.EXIT_POLICY_VIOLATION)
            self.assertEqual(payload["status"], "policy_violation")
            self.assertIn("policy_violation", payload["reason_codes"])

    def test_fail_closed_when_mcp_status_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            args = self._args(repo_root)

            with mock.patch.object(
                orchestrator,
                "get_mcp_status",
                return_value={"ok": False, "status": 0, "payload": {}, "error": "timeout"},
            ):
                code, payload = orchestrator.run(args, environ=self._env())

            self.assertEqual(code, orchestrator.EXIT_MCP_UNAVAILABLE)
            self.assertEqual(payload["status"], "mcp_unavailable")
            self.assertIn("mcp_unavailable", payload["reason_codes"])

    def test_fail_closed_when_required_resource_read_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            args = self._args(repo_root)

            with (
                mock.patch.object(
                    orchestrator,
                    "get_mcp_status",
                    return_value={"ok": True, "status": 200, "payload": self._mcp_status_payload(), "error": ""},
                ),
                mock.patch.object(
                    orchestrator,
                    "read_comfy_resources",
                    return_value={
                        "ok": False,
                        "initialize_ok": True,
                        "resources_list_ok": True,
                        "available_resources": ["shim.comfy.status", "shim.comfy.queue", "shim.comfy.history"],
                        "reads": {
                            "shim.comfy.status": {"ok": True, "error": "", "payload": {}},
                            "shim.comfy.queue": {"ok": False, "error": "read failed", "payload": None},
                            "shim.comfy.history": {"ok": True, "error": "", "payload": {}},
                        },
                        "error": "required resource read failed",
                    },
                ),
            ):
                code, payload = orchestrator.run(args, environ=self._env())

            self.assertEqual(code, orchestrator.EXIT_RESOURCE_UNAVAILABLE)
            self.assertEqual(payload["status"], "resource_unavailable")
            self.assertIn("mcp_unavailable", payload["reason_codes"])

    def test_successful_mocked_run_returns_expected_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            args = self._args(repo_root)
            validation_payload = {
                "status": "ok",
                "reason_codes": [],
                "guidance_hints": [
                    {
                        "resource": "shim.comfy.queue",
                        "finding": "Queue is healthy.",
                        "evidence": ["pending_count=1"],
                        "confidence": 0.95,
                        "priority": "medium",
                    }
                ],
                "checks": {"status_ok": True, "queue_ok": True, "history_ok": True},
                "status_age_seconds": 4.2,
            }

            with (
                mock.patch.object(
                    orchestrator,
                    "get_mcp_status",
                    return_value={"ok": True, "status": 200, "payload": self._mcp_status_payload(), "error": ""},
                ),
                mock.patch.object(
                    orchestrator,
                    "read_comfy_resources",
                    return_value=self._resource_probe_payload(),
                ),
                mock.patch.object(
                    orchestrator,
                    "validate_comfy_resources",
                    return_value=validation_payload,
                ),
            ):
                code, payload = orchestrator.run(args, environ=self._env())

            self.assertEqual(code, orchestrator.EXIT_SUCCESS)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["cloud_fallback_count"], 0)
            self.assertEqual(payload["validation"]["cloud_fallback_count"], 0)
            for key in (
                "status",
                "task_id",
                "mcp_probe",
                "resource_probe",
                "validation",
                "guidance_hints",
                "timing_ms",
                "reason_codes",
                "cloud_fallback_count",
            ):
                self.assertIn(key, payload)

    def test_exit_code_mapping_for_validation_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            args = self._args(repo_root)

            with (
                mock.patch.object(
                    orchestrator,
                    "get_mcp_status",
                    return_value={"ok": True, "status": 200, "payload": self._mcp_status_payload(), "error": ""},
                ),
                mock.patch.object(
                    orchestrator,
                    "read_comfy_resources",
                    return_value=self._resource_probe_payload(),
                ),
                mock.patch.object(
                    orchestrator,
                    "validate_comfy_resources",
                    return_value={
                        "status": "validation_failed",
                        "reason_codes": ["schema_invalid"],
                        "guidance_hints": [],
                    },
                ),
            ):
                code, payload = orchestrator.run(args, environ=self._env())

            self.assertEqual(orchestrator.EXIT_SUCCESS, 0)
            self.assertEqual(orchestrator.EXIT_MCP_UNAVAILABLE, 10)
            self.assertEqual(orchestrator.EXIT_RESOURCE_UNAVAILABLE, 11)
            self.assertEqual(orchestrator.EXIT_VALIDATION_FAILED, 12)
            self.assertEqual(orchestrator.EXIT_POLICY_VIOLATION, 13)
            self.assertEqual(code, orchestrator.EXIT_VALIDATION_FAILED)
            self.assertEqual(payload["status"], "validation_failed")
            self.assertIn("schema_invalid", payload["reason_codes"])


if __name__ == "__main__":
    unittest.main()
