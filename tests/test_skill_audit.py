from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root
        / "skill-candidates"
        / "skill-auditor"
        / "scripts"
        / "skill_audit.py"
    )
    spec = importlib.util.spec_from_file_location("skill_audit", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_skill(
    root: Path,
    name: str,
    description: str,
    body: str,
    *,
    extra_files: dict[str, str] | None = None,
) -> None:
    folder = root / name
    (folder / "agents").mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    (folder / "agents" / "openai.yaml").write_text(
        "interface:\n  display_name: demo\n  short_description: demo\n  default_prompt: demo\n",
        encoding="utf-8",
    )
    for rel, text in (extra_files or {}).items():
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class SkillAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_parse_frontmatter_extracts_required_fields(self) -> None:
        text = "\n".join(
            [
                "---",
                "name: demo-skill",
                "description: Demo description",
                "---",
                "",
                "body line",
            ]
        )
        metadata, body = self.mod.parse_frontmatter(text)
        self.assertEqual(metadata["name"], "demo-skill")
        self.assertEqual(metadata["description"], "Demo description")
        self.assertIn("body line", body)

    def test_main_requires_arbiter_evidence_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(root, "alpha-skill", "alpha", "alpha tokens")
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "alpha-skill",
                "--require-arbiter-evidence",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["high_count"], 1)
            self.assertEqual(payload["findings"][0]["code"], "arbiter_missing")

    def test_classifies_upgrade_with_overlap_and_valid_arbiter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(
                root,
                "alpha-skill",
                "alpha",
                "routing diagnostics endpoint window manager",
            )
            _write_skill(
                root,
                "beta-skill",
                "beta",
                "routing telemetry policy gate",
            )
            arbiter_path = Path(tmp) / "arbiter.json"
            arbiter_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "skill": "alpha-skill",
                                "action": "kept",
                                "persistent_nonzero": False,
                                "max_rg": 0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "alpha-skill",
                "--upgrade-threshold",
                "0.10",
                "--arbiter-report",
                str(arbiter_path),
                "--require-arbiter-evidence",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 0)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["high_count"], 0)
            self.assertEqual(payload["medium_count"], 0)
            self.assertEqual(payload["low_count"], 0)
            self.assertEqual(payload["classifications"][0]["classification"], "upgrade")
            self.assertEqual(payload["classifications"][0]["nearest_peer"], "beta-skill")

    def test_flags_legacy_repo_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(
                root,
                "local-compute-usage",
                "local",
                '$env:REPO_B_CONTINUE_ALLOWED_ROOTS = "$env:USERPROFILE\\Documents\\GitHub\\<PRIVATE_REPO_B>"',
            )
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "local-compute-usage",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in payload["findings"]}
            self.assertIn("legacy_repo_root_alias", codes)

    def test_flags_missing_shim_meta_harness_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(
                root,
                "shim-pc-control-brain-routing",
                "shim",
                "Keep port 9000 stable and research with sub-agents.",
            )
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "shim-pc-control-brain-routing",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in payload["findings"]}
            self.assertIn("shim_hosted_lane_missing", codes)
            self.assertIn("shim_pc_control_local_agent_missing", codes)
            self.assertIn("shim_canonical_root_missing", codes)

    def test_flags_legacy_repo_root_and_non_authoritative_1234_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(
                root,
                "alpha-skill",
                "alpha",
                "Use the canonical repo root, not legacy aliases.",
                extra_files={
                    "notes.md": "Root: $env:USERPROFILE\\Documents\\GitHub\\<PRIVATE_REPO_B>\n",
                    "scripts/check.py": 'BASE_URL = "http://127.0.0.1:1234/v1"\n',
                },
            )
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "alpha-skill",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in payload["findings"]}
            self.assertIn("legacy_repo_root_alias", codes)
            self.assertIn("non_authoritative_1234_authority", codes)

    def test_flags_same_file_legacy_path_even_with_legacy_wording(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            _write_skill(
                root,
                "demo-skill",
                "demo",
                "This legacy migration note still says to use $env:USERPROFILE\\Documents\\GitHub\\demo until later.",
            )
            out_path = Path(tmp) / "audit.json"
            argv = [
                "skill_audit.py",
                "--skills-root",
                str(root),
                "--include-skill",
                "demo-skill",
                "--json-out",
                str(out_path),
                "--format",
                "json",
            ]
            with mock.patch.object(sys, "argv", argv):
                rc = self.mod.main()

            self.assertEqual(rc, 1)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in payload["findings"]}
            self.assertIn("legacy_repo_root_alias", codes)


if __name__ == "__main__":
    unittest.main()
