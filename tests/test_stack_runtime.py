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

    def test_windows_no_window_subprocess_kwargs_sets_hidden_flags(self) -> None:
        class _StartupInfo:
            def __init__(self) -> None:
                self.dwFlags = 0
                self.wShowWindow = 9

        with mock.patch.object(stack_runtime.os, "name", "nt"):
            with mock.patch.object(stack_runtime.subprocess, "STARTUPINFO", _StartupInfo, create=True):
                with mock.patch.object(stack_runtime.subprocess, "STARTF_USESHOWWINDOW", 0x0001, create=True):
                    with mock.patch.object(stack_runtime.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True):
                        payload = stack_runtime._windows_no_window_subprocess_kwargs({"check": False})

        self.assertFalse(payload["check"])
        startup = payload.get("startupinfo")
        self.assertIsNotNone(startup)
        self.assertTrue(int(startup.dwFlags) & 0x0001)
        self.assertEqual(int(startup.wShowWindow), 0)
        self.assertEqual(int(payload.get("creationflags") or 0), 0x08000000)

    def test_powershell_json_uses_hidden_windows_flags(self) -> None:
        completed = mock.Mock(returncode=0, stdout="[]")

        class _StartupInfo:
            def __init__(self) -> None:
                self.dwFlags = 0
                self.wShowWindow = 7

        with mock.patch.object(stack_runtime.os, "name", "nt"):
            with mock.patch(
                "skill_arbiter.stack_runtime.which",
                side_effect=lambda name: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" if name == "powershell.exe" else None,
            ):
                with mock.patch.object(stack_runtime.subprocess, "STARTUPINFO", _StartupInfo, create=True):
                    with mock.patch.object(stack_runtime.subprocess, "STARTF_USESHOWWINDOW", 0x0001, create=True):
                        with mock.patch.object(stack_runtime.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True):
                            with mock.patch.object(stack_runtime.subprocess, "run", return_value=completed) as run_mock:
                                payload = stack_runtime._powershell_json("Get-Process")

        self.assertEqual(payload, [])
        args, kwargs = run_mock.call_args
        self.assertEqual(
            args[0],
            [
                "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-Command",
                "Get-Process",
            ],
        )
        self.assertIn("startupinfo", kwargs)
        self.assertEqual(int(kwargs.get("creationflags") or 0), 0x08000000)

    def test_process_rows_prefer_psutil_over_powershell(self) -> None:
        proc = mock.Mock(info={"name": "python.exe", "pid": 42, "cmdline": ["python.exe", "skill-arbiter", "worker.py"]})
        fake_psutil = mock.Mock()
        fake_psutil.process_iter.return_value = [proc]

        with mock.patch.object(stack_runtime, "psutil", fake_psutil):
            with mock.patch("skill_arbiter.stack_runtime._powershell_json") as shell_mock:
                rows = stack_runtime._process_rows()

        self.assertEqual(rows, [{"Name": "python.exe", "ProcessId": 42, "CommandLine": "python.exe skill-arbiter worker.py"}])
        shell_mock.assert_not_called()

    def test_codex_rows_prefer_psutil_over_powershell(self) -> None:
        proc = mock.Mock(info={"name": "Code.exe", "pid": 77, "cmdline": ["Code.exe", "workspace.code-workspace"]})
        fake_psutil = mock.Mock()
        fake_psutil.process_iter.return_value = [proc]

        with mock.patch.dict(os.environ, {"SKILL_ARBITER_ENABLE_CODEX_WATCH": "1"}, clear=False):
            with mock.patch.object(stack_runtime, "psutil", fake_psutil):
                with mock.patch("skill_arbiter.stack_runtime._powershell_json") as shell_mock:
                    rows = stack_runtime._codex_rows()

        self.assertEqual(rows, [{"Name": "Code.exe", "ProcessId": 77, "CommandLine": "Code.exe workspace.code-workspace"}])
        shell_mock.assert_not_called()

    def test_local_supervision_snapshot_skips_live_advisor_chat_by_default(self) -> None:
        stack_runtime._LOCAL_SUPERVISION_CACHE["expires_at"] = 0.0
        stack_runtime._LOCAL_SUPERVISION_CACHE["payload"] = None

        with mock.patch("skill_arbiter.stack_runtime._process_rows", return_value=[]):
            with mock.patch("skill_arbiter.stack_runtime._codex_rows", return_value=[]):
                with mock.patch("skill_arbiter.stack_runtime.available_models", return_value=["radeon-qwen3.5-4b"]):
                    with mock.patch("skill_arbiter.stack_runtime.advisor_model", return_value="radeon-qwen3.5-4b"):
                        with mock.patch("skill_arbiter.stack_runtime.request_local_advice") as advice_mock:
                            payload = stack_runtime._local_supervision_snapshot()

        advice_mock.assert_not_called()
        self.assertEqual(payload["advisor"]["selected_model"], "radeon-qwen3.5-4b")
        self.assertIn("local Qwen lane", payload["advisor"]["note"])


if __name__ == "__main__":
    unittest.main()
