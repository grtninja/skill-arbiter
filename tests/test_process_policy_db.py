from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from skill_arbiter import process_policy_db
from skill_arbiter.process_policy_db import ProcessPolicyError


class ProcessPolicyDbTests(unittest.TestCase):
    def test_default_rg_policy_allows_one_bounded_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "policy.sqlite3"
            payload = process_policy_db.status(path=db_path)

        policies = {row["executable"]: row for row in payload["policies"]}
        self.assertEqual(payload["integrity"], "ok")
        self.assertEqual(policies["rg.exe"]["action"], "kill_excess")
        self.assertEqual(policies["rg.exe"]["max_instances"], 1)
        self.assertEqual(policies["rg.exe"]["max_age_seconds"], 45)

    def test_denied_subprocess_is_blocked_and_audited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "policy.sqlite3"
            process_policy_db.deny_executable("bad.exe", reason="test deny", path=db_path)

            with self.assertRaises(ProcessPolicyError):
                process_policy_db.enforce_subprocess_policy(["bad.exe", "--version"], path=db_path)

            payload = process_policy_db.status(path=db_path)

        self.assertTrue(any(row["event_type"] == "subprocess_blocked" for row in payload["recent_audit"]))

    def test_kill_excess_keeps_single_young_instance(self) -> None:
        rows = [
            {"Id": 10, "AgeSeconds": 5},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "policy.sqlite3"
            with mock.patch.object(process_policy_db.os, "name", "nt"):
                with mock.patch.object(process_policy_db, "_powershell_process_rows", return_value=rows):
                    with mock.patch.object(process_policy_db.subprocess, "run") as run_mock:
                        payload = process_policy_db.enforce_denied_processes(path=db_path)

        self.assertEqual(payload["actions"], [])
        run_mock.assert_not_called()

    def test_kill_excess_targets_extra_instances(self) -> None:
        rows = [
            {"Id": 10, "AgeSeconds": 5},
            {"Id": 11, "AgeSeconds": 7},
            {"Id": 12, "AgeSeconds": 9},
        ]
        completed = mock.Mock(returncode=0, stdout="")
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "policy.sqlite3"
            with mock.patch.object(process_policy_db.os, "name", "nt"):
                with mock.patch.object(process_policy_db, "_powershell_process_rows", return_value=rows):
                    with mock.patch.object(process_policy_db.subprocess, "run", return_value=completed) as run_mock:
                        payload = process_policy_db.enforce_denied_processes(path=db_path)

        self.assertEqual(payload["actions"][0]["executable"], "rg")
        self.assertEqual(payload["actions"][0]["kill_count"], 2)
        self.assertTrue(run_mock.called)

    def test_kill_excess_targets_over_age_single_instance(self) -> None:
        rows = [
            {"Id": 10, "AgeSeconds": 99},
        ]
        completed = mock.Mock(returncode=0, stdout="")
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "policy.sqlite3"
            with mock.patch.object(process_policy_db.os, "name", "nt"):
                with mock.patch.object(process_policy_db, "_powershell_process_rows", return_value=rows):
                    with mock.patch.object(process_policy_db.subprocess, "run", return_value=completed):
                        payload = process_policy_db.enforce_denied_processes(path=db_path)

        self.assertEqual(payload["actions"][0]["kill_count"], 1)


if __name__ == "__main__":
    unittest.main()
