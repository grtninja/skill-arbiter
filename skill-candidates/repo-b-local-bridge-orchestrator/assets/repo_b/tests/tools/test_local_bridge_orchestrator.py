from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import local_bridge_orchestrator as orchestrator  # noqa: E402


class LocalBridgeOrchestratorTests(unittest.TestCase):
    def test_scope_query_specs_config(self) -> None:
        specs = orchestrator.scope_query_specs("config")
        exts = {item["ext"] for item in specs}
        self.assertEqual(exts, {"yaml", "yml", "json", "toml"})

    def test_should_retry_index(self) -> None:
        run_report = {"status": "partial", "stop_reason": "max_seconds_reached"}
        self.assertTrue(orchestrator.should_retry_index([], run_report))
        self.assertFalse(orchestrator.should_retry_index(["src/service/a.py"], run_report))

    def test_parse_allowed_roots_defaults_to_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir).resolve()
            roots = orchestrator.parse_allowed_roots("", repo_root)
            self.assertEqual(roots, [repo_root])

    def test_run_returns_policy_violation_when_mode_not_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            prompt_path = repo_root / "prompt.txt"
            prompt_path.write_text("Summarize service changes.\n", encoding="utf-8")
            args = argparse.Namespace(
                task="task-1",
                prompt_file=str(prompt_path),
                scope="connector",
                json_out=str(repo_root / "out.json"),
                repo_root=str(repo_root),
                index_dir=".codex-index",
                bridge_url="http://127.0.0.1:9000",
                limit=50,
                timeout_seconds=0.5,
            )
            env = {
                "REPO_B_LOCAL_ORCH_ENABLED": "1",
                "REPO_B_LOCAL_ORCH_FAIL_CLOSED": "1",
                "REPO_B_CONTINUE_BRIDGE_ENABLED": "1",
                "REPO_B_CONTINUE_MODE": "controlled_write",
            }
            code, payload = orchestrator.run(args, environ=env)
            self.assertEqual(code, orchestrator.EXIT_POLICY_VIOLATION)
            self.assertEqual(payload["status"], "policy_violation")
            self.assertIn("policy_violation", payload["reason_codes"])

    def test_run_returns_bridge_unavailable_when_probe_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            prompt_path = repo_root / "prompt.txt"
            prompt_path.write_text("Summarize service changes.\n", encoding="utf-8")
            args = argparse.Namespace(
                task="task-2",
                prompt_file=str(prompt_path),
                scope="service",
                json_out=str(repo_root / "out.json"),
                repo_root=str(repo_root),
                index_dir=".codex-index",
                bridge_url="http://127.0.0.1:9000",
                limit=50,
                timeout_seconds=0.5,
            )
            env = {
                "REPO_B_LOCAL_ORCH_ENABLED": "1",
                "REPO_B_LOCAL_ORCH_FAIL_CLOSED": "1",
                "REPO_B_CONTINUE_BRIDGE_ENABLED": "1",
                "REPO_B_CONTINUE_MODE": "read_only",
            }
            with mock.patch.object(
                orchestrator,
                "probe_bridge",
                return_value={
                    "ok": False,
                    "health": {"ok": False, "status": 0, "error": "timeout", "summary": {}},
                    "capabilities": {"ok": False, "status": 0, "error": "timeout", "summary": {}},
                },
            ):
                code, payload = orchestrator.run(args, environ=env)
            self.assertEqual(code, orchestrator.EXIT_BRIDGE_UNAVAILABLE)
            self.assertEqual(payload["status"], "bridge_unavailable")
            self.assertIn("bridge_unreachable", payload["reason_codes"])


if __name__ == "__main__":
    unittest.main()
