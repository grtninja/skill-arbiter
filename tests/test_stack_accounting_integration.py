from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from skill_arbiter.stack_accounting import normalize_stack_accounting


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str, relative_path: str):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


usage_guard = _load_script(
    "usage_guard_module",
    "skill-candidates/usage-watcher/scripts/usage_guard.py",
)
skill_cost_governor = _load_script(
    "skill_cost_governor_module",
    "skill-candidates/skill-cost-credit-governor/scripts/skill_cost_governor.py",
)
local_compute_preflight = _load_script(
    "local_compute_preflight_module",
    "skill-candidates/local-compute-usage/scripts/local_compute_preflight.py",
)


class StackAccountingIntegrationTests(unittest.TestCase):
    def test_normalize_stack_accounting_uses_summary_fallbacks(self) -> None:
        payload = normalize_stack_accounting(
            {
                "status": "ok",
                "telemetry": {
                    "tpk_preview": 463362648.6236175,
                    "provenance": {
                        "cost_state": "suppressed",
                        "measurement_state": "measured",
                        "token_count_state": "unverified",
                    },
                    "runtime_step": {"latency_ms": 1.4},
                    "lane_status_counts": {"production_real": 1995, "experimental": 5},
                    "lmstudio_routing": {"mode": "hybrid", "traffic_active": True},
                },
            },
            {
                "summary": {
                    "group_count": 1,
                    "groups": [
                        {
                            "provider": "lmstudio",
                            "displacement_value_preview": 4.25,
                            "benchmark_api_equivalent_cost": 4.25,
                        }
                    ],
                }
            },
            health_url="http://127.0.0.1:9000/health",
            summary_url="http://127.0.0.1:9000/api/accounting/summary",
        )
        self.assertTrue(payload["available"])
        self.assertTrue(payload["preview_positive"])
        self.assertEqual(payload["preview_cost_state"], "priced")
        self.assertEqual(payload["displacement_value_preview"], 4.25)
        self.assertEqual(payload["benchmark_api_equivalent_cost"], 4.25)
        self.assertEqual(payload["experimental_route_count"], 5)
        self.assertEqual(payload["tpk"], 463362648.6236175)
        self.assertEqual(payload["tpk_preview"], 463362648.6236175)
        self.assertIsNone(payload["tpk_authoritative"])
        self.assertEqual(payload["tpk_source"], "preview")

    def test_usage_guard_analyze_embeds_stack_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            usage_csv = Path(temp_dir) / "usage.csv"
            usage_csv.write_text(
                "Date,Service,Credits used\n2026-03-11,Extension,10\n2026-03-12,Extension,8\n",
                encoding="utf-8",
            )
            args = Namespace(
                input=str(usage_csv),
                window_days=30,
                daily_budget=20.0,
                weekly_budget=160.0,
                credits_remaining=181.0,
                five_hour_limit_remaining=92.0,
                weekly_limit_remaining=83.0,
                stack_health_url="http://127.0.0.1:9000/health",
                stack_summary_url="http://127.0.0.1:9000/api/accounting/summary",
                stack_timeout_seconds=5.0,
            )
            with mock.patch.object(
                usage_guard,
                "fetch_stack_accounting",
                return_value={
                    "local_ready": True,
                    "tpk": 463362648.6,
                    "authoritative_cost_state": "derived",
                    "preview_cost_state": "priced",
                    "displacement_value_preview": 4.25,
                    "benchmark_api_equivalent_cost": 4.25,
                    "preview_positive": True,
                    "runtime_latency_ms": 1.4,
                },
            ):
                report = usage_guard.analyze_usage(args)
        self.assertIn("stack_evidence", report)
        self.assertTrue(report["stack_evidence"]["preview_positive"])
        self.assertTrue(
            any("displacing benchmark API cost" in item for item in report["recommendations"])
        )

    def test_skill_cost_governor_flags_remote_heavy_when_local_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "usage.json"
            input_path.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "timestamp": "2026-03-12T12:00:00Z",
                                "skill": "usage-watcher",
                                "caller_skill": "skill-hub",
                                "total_tokens": 1200,
                                "credits": 9.5,
                                "runtime_ms": 800,
                                "status": "success",
                                "provider": "openai",
                                "local_execution": False,
                            },
                            {
                                "timestamp": "2026-03-12T12:10:00Z",
                                "skill": "usage-watcher",
                                "caller_skill": "skill-hub",
                                "total_tokens": 1100,
                                "credits": 8.0,
                                "runtime_ms": 780,
                                "status": "success",
                                "provider": "openai",
                                "local_execution": False,
                            },
                            {
                                "timestamp": "2026-03-12T12:20:00Z",
                                "skill": "usage-watcher",
                                "caller_skill": "skill-hub",
                                "total_tokens": 900,
                                "credits": 7.0,
                                "runtime_ms": 750,
                                "status": "success",
                                "provider": "mx3",
                                "local_execution": True,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            args = Namespace(
                input=str(input_path),
                window_days=30,
                credits_per_1k_tokens=0.0,
                soft_daily_budget=12.0,
                hard_daily_budget=30.0,
                soft_window_budget=100.0,
                hard_window_budget=200.0,
                spike_multiplier=2.0,
                loop_threshold=6,
                chatter_threshold=20,
                max_runtime_ms=45000.0,
                stack_health_url="http://127.0.0.1:9000/health",
                stack_summary_url="http://127.0.0.1:9000/api/accounting/summary",
                stack_timeout_seconds=5.0,
            )
            with mock.patch.object(
                skill_cost_governor,
                "fetch_stack_accounting",
                return_value={
                    "local_ready": True,
                    "preview_positive": True,
                    "displacement_value_preview": 4.25,
                    "preview_cost_state": "priced",
                    "authoritative_cost_state": "derived",
                    "tpk": 463362648.6,
                },
            ):
                report = skill_cost_governor.analyze(args)
        self.assertIn("stack_evidence", report)
        skill_row = report["skills"][0]
        self.assertIn("remote_heavy_when_local_available", skill_row["reason_codes"])
        self.assertIn(skill_row["proposed_action"], {"throttle", "disable"})

    def test_local_compute_preflight_writes_stack_evidence(self) -> None:
        payload: dict[str, object]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "preflight.json"
            argv = [
                "local_compute_preflight.py",
                "--workspace-root",
                str(REPO_ROOT),
                "--stack-health-url",
                "http://127.0.0.1:9000/health",
                "--stack-summary-url",
                "http://127.0.0.1:9000/api/accounting/summary",
                "--json-out",
                str(output_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                with mock.patch.object(local_compute_preflight.shutil, "which", return_value="C:\\Windows\\System32\\code.exe"):
                    with mock.patch.object(local_compute_preflight, "run_cmd", return_value=(0, "1.99.0")):
                        with mock.patch.object(
                            local_compute_preflight,
                            "fetch_stack_accounting",
                            return_value={
                                "local_ready": True,
                                "preview_positive": True,
                                "displacement_value_preview": 4.25,
                                "tpk": 463362648.6,
                            },
                        ):
                            result = local_compute_preflight.main()
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        self.assertTrue(payload["summary"]["stack_evidence_available"])
        self.assertTrue(payload["stack_evidence"]["preview_positive"])


if __name__ == "__main__":
    unittest.main()
