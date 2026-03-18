from __future__ import annotations

import json
import os
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
from urllib import error, request

from skill_arbiter.agent_server import NullClawState, build_handler
from skill_arbiter.inventory import _recent_work_skill_names, _review_fingerprint, build_inventory_snapshot
from skill_arbiter.llm_advisor import advisor_model
from skill_arbiter.mitigation import plan_case, reconcile_cases


def _write_skill(root: Path, name: str, description: str = "demo skill") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "---",
                "",
                "body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return skill_dir


class InventorySnapshotTests(unittest.TestCase):
    def test_recent_work_skill_names_reads_radar_payloads_and_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_root = root / "skill-candidates"
            (root / "references").mkdir()
            candidate_root.mkdir()
            (candidate_root / "alpha").mkdir()
            (candidate_root / "gamma").mkdir()
            radar_payload = {
                "repos": [
                    {
                        "changed_files_sample": [
                            "alpha/src/render_notes.txt",
                            "third_party/notes.md",
                        ],
                        "dirty_files_sample": ["x", "tools/gamma-review.patch"],
                        "skill_paths": ["scripts/alpha_setup.py"],
                        "commits_sample": [{"subject": "Reviewed gamma and alpha in one pass"}],
                    }
                ]
            }
            (root / "references" / "cross_repo_open_work_radar_20260317.json").write_text(
                json.dumps(radar_payload),
                encoding="utf-8",
            )

            with mock.patch("skill_arbiter.inventory.REPO_ROOT", root):
                recent_work = _recent_work_skill_names(candidate_root)

        self.assertEqual(recent_work, {"alpha", "gamma"})

    def test_build_inventory_snapshot_reconciles_openai_baseline_and_overlay_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(skills_root, "alpha", "installed alpha")
            _write_skill(candidate_root, "beta", "candidate beta")
            cache_path = root / "inventory.json"

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": ["alpha", "gamma"], "system": ["skill-creator"], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                        with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value={"beta"}):
                                with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                    with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                        with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                            with mock.patch("skill_arbiter.inventory._evaluate_skill_dir", return_value=("low", [])):
                                                payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            self.assertEqual(payload["host_id"], "host1234")
            self.assertEqual(payload["advisor_note"], "Use the local Qwen lane.")
            rows = {row["name"]: row for row in payload["skills"]}
            self.assertEqual(rows["alpha"]["source_type"], "installed_skill")
            self.assertEqual(rows["alpha"]["origin"], "openai_builtin")
            self.assertEqual(rows["alpha"]["ownership"], "official_builtin")
            self.assertEqual(rows["alpha"]["legitimacy_status"], "official_trusted")
            self.assertEqual(rows["beta"]["source_type"], "overlay_candidate")
            self.assertEqual(rows["beta"]["ownership"], "repo_owned_candidate")
            self.assertEqual(rows["beta"]["legitimacy_status"], "owned_trusted")
            self.assertIn("recent_work_relevant", rows["beta"]["notes"])
            self.assertEqual(rows["gamma"]["source_type"], "openai_builtin_baseline")
            self.assertEqual(rows["gamma"]["drift_state"], "missing_local_builtin")
            self.assertIn("legitimacy_summary", payload)
            self.assertTrue(cache_path.is_file())

    def test_official_builtin_skill_is_trusted_by_baseline_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(skills_root, "cloudflare-deploy", "installed official sensitive skill")
            cache_path = root / "inventory.json"

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": ["cloudflare-deploy"], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                        with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                    with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                        with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                            with mock.patch(
                                                "skill_arbiter.inventory._evaluate_skill_dir",
                                                return_value=("critical", ["curl_pipe_shell"], [{"code": "curl_pipe_shell", "title": "curl piped to shell"}]),
                                            ):
                                                payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            row = next(item for item in payload["skills"] if item["name"] == "cloudflare-deploy")
            self.assertEqual(row["ownership"], "official_builtin")
            self.assertEqual(row["legitimacy_status"], "official_trusted")
            self.assertEqual(row["risk_class"], "low")
            self.assertEqual(payload["legitimacy_summary"]["blocked_hostile"], 0)

    def test_third_party_attribution_keeps_imported_skill_trusted_but_provenance_tracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            cache_path = root / "inventory.json"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(skills_root, "clawhub", "installed imported skill")

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": [], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                        with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                    with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                        with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                            with mock.patch(
                                                "skill_arbiter.inventory._parse_third_party_skill_attribution",
                                                return_value={
                                                    "clawhub": {
                                                        "origin_skill": "clawhub",
                                                        "source_label": "openclaw",
                                                        "intake_recommendation": "admit",
                                                        "origin_path": "<THIRD_PARTY_CLONES>/openclaw/skills/clawhub",
                                                    }
                                                },
                                            ):
                                                with mock.patch(
                                                    "skill_arbiter.inventory._evaluate_skill_dir",
                                                    return_value=("critical", ["global_install_command"], [{"code": "global_install_command", "title": "global install"}]),
                                                ):
                                                    payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            row = next(item for item in payload["skills"] if item["name"] == "clawhub")
            self.assertEqual(row["ownership"], "third_party_imported")
            self.assertEqual(row["legitimacy_status"], "third_party_trusted")
            self.assertEqual(row["risk_class"], "low")
            self.assertEqual(row["recommended_action"], "keep")

    def test_rejected_third_party_skill_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            cache_path = root / "inventory.json"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(skills_root, "xurl", "installed rejected imported skill")

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": [], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                        with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                    with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                        with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                            with mock.patch(
                                                "skill_arbiter.inventory._parse_third_party_skill_attribution",
                                                return_value={
                                                    "xurl": {
                                                        "origin_skill": "xurl",
                                                        "source_label": "openclaw",
                                                        "intake_recommendation": "reject",
                                                        "origin_path": "<THIRD_PARTY_CLONES>/openclaw/skills/xurl",
                                                    }
                                                },
                                            ):
                                                with mock.patch(
                                                    "skill_arbiter.inventory._evaluate_skill_dir",
                                                    return_value=("low", [], []),
                                                ):
                                                    payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            row = next(item for item in payload["skills"] if item["name"] == "xurl")
            self.assertEqual(row["ownership"], "third_party_imported")
            self.assertEqual(row["legitimacy_status"], "blocked_hostile")
            self.assertEqual(row["recommended_action"], "quarantine")

    def test_reviewed_sensitive_skill_can_be_accepted_locally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            cache_path = root / "inventory.json"
            accepted_path = root / "accepted-risk.json"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(skills_root, "acp-router", "installed owned sensitive skill")
            review_fingerprint = _review_fingerprint(
                name="acp-router",
                ownership="local_unowned",
                source_type="installed_skill",
                origin="overlay_or_local",
                drift_state="local_only",
                codes=["cross_agent_remote_install"],
            )
            accepted_path.write_text(
                json.dumps(
                    {
                        "accepted_subjects": {
                            "acp-router": {
                                "review_fingerprint": review_fingerprint,
                                "ownership": "local_unowned",
                                "legitimacy_status": "manual_review",
                                "reason": "accepted for local host",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": [], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_third_party_skill_attribution", return_value={}):
                        with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                                with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                    with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                        with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                            with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                                with mock.patch("skill_arbiter.accepted_risk.accepted_risk_path", return_value=accepted_path):
                                                    with mock.patch(
                                                        "skill_arbiter.inventory._evaluate_skill_dir",
                                                        return_value=("critical", ["cross_agent_remote_install"], [{"code": "cross_agent_remote_install", "title": "cross-agent remote install"}]),
                                                    ):
                                                        payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            row = next(item for item in payload["skills"] if item["name"] == "acp-router")
            self.assertEqual(row["legitimacy_status"], "manual_accepted")
            self.assertEqual(row["risk_class"], "accepted")
            self.assertEqual(row["recommended_action"], "keep")
            self.assertEqual(payload["incident_count"], 0)
            self.assertEqual(payload["legitimacy_summary"]["accepted_review"], 1)

    def test_candidate_review_does_not_raise_active_host_incident(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            cache_path = root / "inventory.json"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(candidate_root, "clawhub", "candidate only skill")

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": [], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_third_party_skill_attribution", return_value={}):
                        with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                                with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                    with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                        with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                            with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                                with mock.patch(
                                                    "skill_arbiter.inventory._evaluate_skill_dir",
                                                    return_value=("critical", ["global_install_command"], [{"code": "global_install_command", "title": "global install"}]),
                                                ):
                                                    payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            row = next(item for item in payload["skills"] if item["name"] == "clawhub")
            self.assertEqual(row["source_type"], "overlay_candidate")
            self.assertEqual(row["legitimacy_status"], "owned_trusted")
            self.assertEqual(row["risk_class"], "low")
            self.assertEqual(payload["incident_count"], 0)

    def test_rejected_third_party_candidate_is_kept_out_of_active_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_root = root / "skills"
            candidate_root = root / "skill-candidates"
            cache_path = root / "inventory.json"
            skills_root.mkdir()
            candidate_root.mkdir()
            _write_skill(candidate_root, "xurl", "candidate only rejected skill")

            with mock.patch("skill_arbiter.inventory.fetch_openai_baseline", return_value={"top_level": [], "system": [], "sha": "abc123", "status": "online"}):
                with mock.patch("skill_arbiter.inventory._parse_third_party_sources", return_value=[]):
                    with mock.patch("skill_arbiter.inventory._parse_threat_matrix_sources", return_value=[]):
                        with mock.patch("skill_arbiter.inventory.scan_interop_sources", return_value=[]):
                            with mock.patch("skill_arbiter.inventory._recent_work_skill_names", return_value=set()):
                                with mock.patch("skill_arbiter.inventory.request_local_advice", return_value="Use the local Qwen lane."):
                                    with mock.patch("skill_arbiter.inventory.inventory_cache_path", return_value=cache_path):
                                        with mock.patch("skill_arbiter.inventory.host_id", return_value="host1234"):
                                            with mock.patch(
                                                "skill_arbiter.inventory._parse_third_party_skill_attribution",
                                                return_value={
                                                    "xurl": {
                                                        "origin_skill": "xurl",
                                                        "source_label": "openclaw",
                                                        "intake_recommendation": "reject",
                                                        "origin_path": "<THIRD_PARTY_CLONES>/openclaw/skills/xurl",
                                                    }
                                                },
                                            ):
                                                with mock.patch(
                                                    "skill_arbiter.inventory._evaluate_skill_dir",
                                                    return_value=("critical", ["global_install_command"], [{"code": "global_install_command", "title": "global install"}]),
                                                ):
                                                    payload = build_inventory_snapshot(skills_root=skills_root, candidate_root=candidate_root)

            self.assertFalse(any(item["name"] == "xurl" for item in payload["skills"]))
            self.assertEqual(payload["incident_count"], 0)
            self.assertEqual(payload["legitimacy_summary"]["blocked_hostile"], 0)


class AgentServerTests(unittest.TestCase):
    def test_inventory_refresh_is_throttled(self) -> None:
        state = NullClawState(skills_root=Path("/tmp"), candidate_root=Path("/tmp/skill-candidates"))
        base_payload = {
            "host_id": "host1234",
            "skill_count": 1,
            "source_count": 1,
            "incident_count": 0,
            "legitimacy_summary": {"official_trusted": 0, "owned_trusted": 0, "accepted_review": 0, "needs_review": 0, "blocked_hostile": 0},
            "skills": [],
            "sources": [],
            "incidents": [],
        }
        with mock.patch("skill_arbiter.agent_server.load_poll_profile", return_value={"passive_inventory_ms": 120000}):
            with mock.patch("skill_arbiter.agent_server.build_inventory_snapshot", return_value=base_payload) as build_snapshot:
                with mock.patch("skill_arbiter.agent_server.reconcile_cases") as reconcile_cases:
                    first = state.inventory_refresh()
                    second = state.inventory_refresh()
            self.assertFalse(first["refresh_cached"])
            self.assertTrue(second["refresh_cached"])
            self.assertEqual(build_snapshot.call_count, 1)
            self.assertEqual(reconcile_cases.call_count, 1)

    def test_loopback_api_serves_health_checks_and_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = NullClawState(skills_root=root / "skills", candidate_root=root / "skill-candidates")
            state.run_self_checks = mock.Mock(
                return_value={
                    "host_id": "host1234",
                    "privacy_passed": True,
                    "privacy_findings": [],
                    "self_governance": {"passed": True, "critical_count": 0, "high_count": 0, "findings": []},
                }
            )
            state.inventory_refresh = mock.Mock(
                return_value={
                    "host_id": "host1234",
                    "skill_count": 2,
                    "source_count": 1,
                    "incident_count": 0,
                    "legitimacy_summary": {"official_trusted": 1, "owned_trusted": 1, "accepted_review": 0, "needs_review": 0, "blocked_hostile": 0},
                    "skills": [{"name": "alpha"}],
                    "sources": [{"source_id": "openai-skills"}],
                    "incidents": [],
                }
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(state))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with mock.patch(
                    "skill_arbiter.agent_server.load_cached_inventory",
                    return_value={
                        "skills": [
                            {
                                "name": "alpha",
                                "ownership": "repo_owned",
                                "legitimacy_status": "owned_sensitive",
                                "legitimacy_reason": "owned skill accepted for local host",
                                "review_fingerprint": "alpha-review-1234",
                            }
                        ],
                        "sources": [],
                        "incidents": [],
                    },
                ):
                    with mock.patch("skill_arbiter.agent_server.read_audit_events", return_value=[]):
                        with mock.patch(
                            "skill_arbiter.agent_server.load_cached_public_readiness",
                            return_value={"passed": True, "critical_count": 0, "high_count": 0, "medium_count": 0, "findings": []},
                        ):
                            with mock.patch("skill_arbiter.agent_server.list_cases", return_value=[]):
                                with mock.patch("skill_arbiter.agent_server.plan_case", return_value={"case_id": "mitigation-alpha", "subject": "alpha"}):
                                    with mock.patch(
                                        "skill_arbiter.agent_server.execute_case_action",
                                        return_value={"case": {"case_id": "mitigation-alpha", "subject": "alpha"}, "outcome": {"recorded": True}},
                                    ):
                                        with mock.patch("skill_arbiter.agent_server.skill_game_status_payload", return_value={"level": 4, "total_xp": 900, "recommended_targets": [{"name": "alpha"}], "recent_events": []}):
                                            with mock.patch(
                                                "skill_arbiter.agent_server.record_skill_game_payload",
                                                return_value={"xp_delta": 125, "clear_run": True, "recommended_targets": [{"name": "alpha"}], "breakdown": []},
                                            ):
                                                with mock.patch(
                                                    "skill_arbiter.agent_server.collaboration_status_payload",
                                                    return_value={
                                                        "event_count": 1,
                                                        "stable_event_count": 1,
                                                        "recent_events": [{"task": "stack reconcile", "outcome": "success"}],
                                                        "recommended_skill_work": [{"name": "heterogeneous-stack-validation", "action": "create", "score": 3}],
                                                        "inventory_targets": [{"name": "alpha"}],
                                                        "trust_ledger_available": True,
                                                    },
                                                ):
                                                    with mock.patch(
                                                        "skill_arbiter.agent_server.record_collaboration_payload",
                                                        return_value={
                                                            "event": {"task": "stack reconcile", "outcome": "success"},
                                                            "event_written": True,
                                                            "trust_ledger": {"available": True, "records": []},
                                                            "event_count": 1,
                                                            "stable_event_count": 1,
                                                            "recent_events": [{"task": "stack reconcile", "outcome": "success"}],
                                                            "recommended_skill_work": [{"name": "heterogeneous-stack-validation", "action": "create", "score": 3}],
                                                            "inventory_targets": [{"name": "alpha"}],
                                                            "trust_ledger_available": True,
                                                        },
                                                    ):
                                                        with mock.patch("skill_arbiter.agent_server.release_quarantine") as release_quarantine:
                                                            release_quarantine.return_value = mock.Mock(to_dict=lambda: {"action": "release_quarantine"})
                                                            with mock.patch("skill_arbiter.agent_server.accept_subject") as accept_subject:
                                                                accept_subject.return_value = mock.Mock(to_dict=lambda: {"action": "accept_review"})
                                                                with mock.patch("skill_arbiter.agent_server.revoke_subject") as revoke_subject:
                                                                    revoke_subject.return_value = mock.Mock(to_dict=lambda: {"action": "revoke_accept_review"})
                                                                    with request.urlopen(f"{base}/v1/health", timeout=3) as response:
                                                                        self.assertEqual(response.headers.get("Cache-Control"), "no-store, max-age=0")
                                                                        self.assertEqual(response.headers.get("Pragma"), "no-cache")
                                                                        health = json.loads(response.read().decode("utf-8"))
                                                                    with request.urlopen(
                                                                        request.Request(
                                                                            f"{base}/v1/health",
                                                                            headers={"Origin": "http://127.0.0.1:3000"},
                                                                            method="GET",
                                                                        ),
                                                                        timeout=3,
                                                                    ) as response:
                                                                        self.assertEqual(
                                                                            response.headers.get("Access-Control-Allow-Origin"),
                                                                            "http://127.0.0.1:3000",
                                                                        )
                                                                    with request.urlopen(
                                                                        request.Request(
                                                                            f"{base}/v1/health",
                                                                            headers={"Origin": "null"},
                                                                            method="GET",
                                                                        ),
                                                                        timeout=3,
                                                                    ) as response:
                                                                        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "null")
                                                                    with self.assertRaises(error.HTTPError) as blocked_origin:
                                                                        request.urlopen(
                                                                            request.Request(
                                                                                f"{base}/v1/health",
                                                                                headers={"Origin": "https://example.com"},
                                                                                method="GET",
                                                                            ),
                                                                            timeout=3,
                                                                        )
                                                                    self.assertEqual(blocked_origin.exception.code, 403)
                                                                    about = json.loads(request.urlopen(f"{base}/v1/about", timeout=3).read().decode("utf-8"))
                                                                    readiness = json.loads(request.urlopen(f"{base}/v1/public-readiness", timeout=3).read().decode("utf-8"))
                                                                    with request.urlopen(f"{base}/v1/skill-game/status", timeout=3) as response:
                                                                        self.assertEqual(response.headers.get("Cache-Control"), "no-store, max-age=0")
                                                                        skill_game_status = json.loads(response.read().decode("utf-8"))
                                                                    collaboration_status = json.loads(request.urlopen(f"{base}/v1/collaboration/status", timeout=3).read().decode("utf-8"))
                                                                    checks = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/self-checks/run", data=b"{}", headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    inventory = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/inventory/refresh", data=b"{}", headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    skill_game_record = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(
                                                                                f"{base}/v1/skill-game/record",
                                                                                data=b'{\"task\":\"inventory_refresh\",\"required_skills\":[\"skill-hub\"],\"used_skills\":[\"skill-hub\"],\"enforcer_pass\":true}',
                                                                                headers={"Content-Type": "application/json"},
                                                                                method="POST",
                                                                            ),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    collaboration_record = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(
                                                                                f"{base}/v1/collaboration/record",
                                                                                data=b'{\"task\":\"stack reconcile\",\"outcome\":\"success\",\"collaborators\":[\"codex\",\"skill-arbiter\"],\"repo_scope\":[\"skill-arbiter\",\"pc-control\"],\"skills_used\":[\"skill-enforcer\"],\"proposed_skill_work\":[{\"name\":\"heterogeneous-stack-validation\",\"action\":\"create\",\"reason\":\"repeatable stack probe workflow\"}],\"stability\":\"stable\"}',
                                                                                headers={"Content-Type": "application/json"},
                                                                                method="POST",
                                                                            ),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    cases = json.loads(request.urlopen(f"{base}/v1/mitigation/cases", timeout=3).read().decode("utf-8"))
                                                                    plan = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/mitigation/plan", data=b'{\"subject\":\"alpha\"}', headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    execute = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/mitigation/execute", data=b'{\"case_id\":\"mitigation-alpha\",\"action\":\"quarantine\"}', headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    release = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/quarantine/release", data=b'{\"skill_name\":\"alpha\"}', headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    accept = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/review/accept", data=b'{\"subject\":\"alpha\"}', headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    revoke = json.loads(
                                                                        request.urlopen(
                                                                            request.Request(f"{base}/v1/review/revoke", data=b'{\"subject\":\"alpha\"}', headers={"Content-Type": "application/json"}, method="POST"),
                                                                            timeout=3,
                                                                        ).read().decode("utf-8")
                                                                    )
                                                                    audit = json.loads(request.urlopen(f"{base}/v1/audit-log", timeout=3).read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

            self.assertEqual(health["status"], "ok")
            self.assertEqual(about["application"], "Skill Arbiter Security Console")
            self.assertTrue(readiness["passed"])
            self.assertEqual(skill_game_status["level"], 4)
            self.assertEqual(collaboration_status["event_count"], 1)
            self.assertTrue(checks["privacy_passed"])
            self.assertEqual(inventory["skill_count"], 2)
            self.assertEqual(skill_game_record["xp_delta"], 125)
            self.assertTrue(skill_game_record["clear_run"])
            self.assertTrue(collaboration_record["event_written"])
            self.assertEqual(collaboration_record["recommended_skill_work"][0]["name"], "heterogeneous-stack-validation")
            self.assertEqual(cases["cases"], [])
            self.assertEqual(plan["case"]["case_id"], "mitigation-alpha")
            self.assertEqual(execute["outcome"]["recorded"], True)
            self.assertEqual(release["decision"]["action"], "release_quarantine")
            self.assertEqual(accept["decision"]["action"], "accept_review")
            self.assertEqual(revoke["decision"]["action"], "revoke_accept_review")
            self.assertEqual(audit["events"], [])


class MitigationTests(unittest.TestCase):
    def test_plan_case_branches_hostile_vs_rebuildable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory = {
                "skills": [
                    {
                        "name": "clawhub",
                        "source_type": "installed_skill",
                        "origin": "overlay_candidate_installed",
                        "risk_class": "critical",
                        "legitimacy_status": "blocked_hostile",
                        "finding_codes": ["curl_pipe_shell", "global_install_command"],
                    },
                    {
                        "name": "repo-safe-skill",
                        "source_type": "overlay_candidate",
                        "origin": "skill_candidates",
                        "risk_class": "high",
                        "finding_codes": ["backup_python_script"],
                    },
                ],
                "incidents": [
                    {"subject": "clawhub", "severity": "critical", "evidence_codes": ["curl_pipe_shell"]},
                    {"subject": "repo-safe-skill", "severity": "high", "evidence_codes": ["backup_python_script"]},
                ],
            }
            with mock.patch("skill_arbiter.mitigation.mitigation_cases_root", return_value=Path(tmp)):
                with mock.patch("skill_arbiter.mitigation.host_id", return_value="host1234"):
                    hostile_case = plan_case("clawhub", inventory)
                    rebuild_case = plan_case("repo-safe-skill", inventory)

            self.assertEqual(hostile_case["classification"], "hostile")
            self.assertTrue(hostile_case["hostile"])
            self.assertEqual(rebuild_case["classification"], "legit_rebuildable")
            self.assertTrue(rebuild_case["rebuildable"])

    def test_reconcile_cases_removes_resolved_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory = {
                "skills": [
                    {
                        "name": "alpha",
                        "source_type": "installed_skill",
                        "origin": "overlay_candidate_installed",
                        "risk_class": "high",
                        "legitimacy_status": "owned_sensitive",
                        "finding_codes": ["global_install_command"],
                    },
                ],
                "incidents": [
                    {"subject": "alpha", "severity": "high", "evidence_codes": ["global_install_command"]},
                ],
            }
            with mock.patch("skill_arbiter.mitigation.mitigation_cases_root", return_value=Path(tmp)):
                with mock.patch("skill_arbiter.mitigation.host_id", return_value="host1234"):
                    plan_case("alpha", inventory)
                    stale = Path(tmp) / "mitigation-stale.json"
                    stale.write_text('{"case_id":"mitigation-stale","subject":"stale","severity":"critical"}\n', encoding="utf-8")
                    rows = reconcile_cases(inventory)

            subjects = {row["subject"] for row in rows}
            self.assertIn("alpha", subjects)
            self.assertFalse(stale.exists())


class AdvisorSelectionTests(unittest.TestCase):
    def test_default_prefers_shared_qwen_lane(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(advisor_model(), "radeon-qwen3.5-4b")

    def test_auto_prefers_local_qwen_coding_model(self) -> None:
        response = mock.MagicMock()
        response.read.return_value = json.dumps(
            {
                "data": [
                    {"id": "phi-4-mini"},
                    {"id": "qwen2.5-coder-7b-instruct"},
                    {"id": "deepseek-coder-lite"},
                ]
            }
        ).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with mock.patch("skill_arbiter.llm_advisor.enabled", return_value=True):
            with mock.patch("skill_arbiter.llm_advisor._local_only", return_value=True):
                with mock.patch("skill_arbiter.llm_advisor._default_base_url", return_value="http://127.0.0.1:9000/v1"):
                    with mock.patch("skill_arbiter.llm_advisor._default_model", return_value="auto"):
                        with mock.patch("skill_arbiter.llm_advisor.request.urlopen", return_value=response):
                            with mock.patch("skill_arbiter.llm_advisor._cached_available_models", return_value=("phi-4-mini", "qwen2.5-coder-7b-instruct", "deepseek-coder-lite")):
                                self.assertEqual(advisor_model(), "qwen2.5-coder-7b-instruct")


if __name__ == "__main__":
    unittest.main()
