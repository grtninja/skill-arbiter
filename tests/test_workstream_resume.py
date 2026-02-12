from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root
        / "skill-candidates"
        / "request-loopback-resume"
        / "scripts"
        / "workstream_resume.py"
    )
    spec = importlib.util.spec_from_file_location("workstream_resume", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkstreamResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_run_init_deduplicates_lanes_and_sets_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            args = argparse.Namespace(
                state_file=str(state_path),
                task="Test workflow",
                lane=["plan", "plan", "implement"],
                in_progress="implement",
                json_out="",
            )
            state = self.mod.run_init(args)
            self.assertEqual(state["task"], "Test workflow")
            self.assertEqual([row["name"] for row in state["lanes"]], ["plan", "implement"])
            self.assertEqual([row["status"] for row in state["lanes"]], ["pending", "in_progress"])

    def test_run_set_updates_lane_and_attaches_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            init_args = argparse.Namespace(
                state_file=str(state_path),
                task="Set workflow",
                lane=["lane_a", "lane_b"],
                in_progress="",
                json_out="",
            )
            self.mod.run_init(init_args)

            set_args = argparse.Namespace(
                state_file=str(state_path),
                lane_status=["lane_a=in_progress"],
                lane_next=["lane_a=run regression checks"],
                artifact=["/tmp/evidence-a.json"],
                note="updated lane",
                json_out="",
            )
            state = self.mod.run_set(set_args)
            lanes = {row["name"]: row for row in state["lanes"]}
            self.assertEqual(lanes["lane_a"]["status"], "in_progress")
            self.assertEqual(lanes["lane_a"]["next_step"], "run regression checks")
            self.assertIn("/tmp/evidence-a.json", lanes["lane_a"]["artifacts"])

    def test_run_resume_reports_continue_start_and_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"

            state_continue = {
                "task": "Continue lane",
                "lanes": [
                    {"name": "a", "status": "in_progress", "next_step": "continue a"},
                    {"name": "b", "status": "pending", "next_step": "do b"},
                ],
            }
            state_path.write_text(json.dumps(state_continue), encoding="utf-8")
            out_continue = self.mod.run_resume(argparse.Namespace(state_file=str(state_path), json_out=""))
            self.assertEqual(out_continue["action"], "continue")
            self.assertEqual(out_continue["lane"], "a")

            state_start = {
                "task": "Start lane",
                "lanes": [
                    {"name": "a", "status": "completed", "next_step": ""},
                    {"name": "b", "status": "pending", "next_step": "do b"},
                ],
            }
            state_path.write_text(json.dumps(state_start), encoding="utf-8")
            out_start = self.mod.run_resume(argparse.Namespace(state_file=str(state_path), json_out=""))
            self.assertEqual(out_start["action"], "start")
            self.assertEqual(out_start["lane"], "b")

            state_blocked = {
                "task": "Blocked lane",
                "lanes": [
                    {"name": "a", "status": "blocked", "next_step": "await dependency"},
                    {"name": "b", "status": "completed", "next_step": ""},
                ],
            }
            state_path.write_text(json.dumps(state_blocked), encoding="utf-8")
            out_blocked = self.mod.run_resume(argparse.Namespace(state_file=str(state_path), json_out=""))
            self.assertEqual(out_blocked["action"], "blocked")

    def test_validate_state_detects_multiple_in_progress(self) -> None:
        state = {
            "lanes": [
                {"name": "a", "status": "in_progress"},
                {"name": "b", "status": "in_progress"},
            ]
        }
        ok, errors, counts = self.mod.validate_state(state)
        self.assertFalse(ok)
        self.assertIn("more than one lane is in_progress", errors)
        self.assertEqual(counts["in_progress"], 2)


if __name__ == "__main__":
    unittest.main()
