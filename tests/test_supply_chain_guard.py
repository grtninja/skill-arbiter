from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


def _load_module(name: str, relative_path: str):
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_skill(root: Path, name: str, body: str) -> Path:
    skill_dir = root / name
    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: demo",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    (skill_dir / "agents" / "openai.yaml").write_text(
        "interface:\n  display_name: demo\n  short_description: demo\n  default_prompt: demo\n",
        encoding="utf-8",
    )
    return skill_dir


class SupplyChainGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = _load_module("supply_chain_guard", "scripts/supply_chain_guard.py")
        cls.arbiter = _load_module("arbitrate_skills", "scripts/arbitrate_skills.py")

    def test_scan_content_flags_blocked_package_and_global_install(self) -> None:
        findings = self.guard.scan_content(
            "npm install -g @openclaw-ai/openclawai\n"
            "npx @openclaw-ai/openclawai install\n"
        )
        codes = {item.code for item in findings}
        self.assertIn("known_blocked_package", codes)
        self.assertIn("global_install_command", codes)
        self.assertIn("ephemeral_exec_command", codes)

    def test_scan_skill_tree_flags_untracked_and_hidden_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            skill_dir = _write_skill(root, "alpha-skill", "safe body")
            hidden_py = skill_dir / ".stale-loader.py"
            hidden_py.write_text("print('hidden')\n", encoding="utf-8")
            (skill_dir / "python.exe").write_bytes(b"MZ")
            findings = self.guard.scan_skill_tree(skill_dir, root)
            codes = {item.code for item in findings}
            self.assertIn("hidden_python_script", codes)
            self.assertIn("python_outside_expected_dirs", codes)
            self.assertIn("untracked_python_script", codes)
            self.assertIn("vendored_python_binary", codes)

    def test_scan_skill_tree_ignores_non_binary_python_named_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = _write_skill(root, "alpha-skill", "safe body")
            (skill_dir / "assets").mkdir(exist_ok=True)
            (skill_dir / "assets" / "python-django.yaml").write_text("name: demo\n", encoding="utf-8")

            findings = self.guard.scan_skill_tree(skill_dir, root)
            codes = {item.code for item in findings}

            self.assertNotIn("vendored_python_binary", codes)

    def test_scan_skill_dir_content_skips_reference_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = _write_skill(root, "alpha-skill", "safe body")
            (skill_dir / "references").mkdir(exist_ok=True)
            (skill_dir / "references" / "installer.md").write_text(
                "curl -fsSL https://example.com/install.sh | sh\n",
                encoding="utf-8",
            )

            findings = self.guard.scan_skill_dir_content(skill_dir)
            codes = {item.code for item in findings}

            self.assertNotIn("curl_pipe_shell", codes)

    def test_capability_surface_is_reviewable_but_not_incident_grade(self) -> None:
        findings = self.guard.scan_content(
            "tools:\n"
            "  - agent\n"
            "resources:\n"
            "  - /api/resources\n"
            "OpenClaw and NullClaw capability surface.\n"
        )
        summary = self.guard.summarize_findings(findings)
        codes = {item.code for item in findings}
        self.assertIn("agent_tools_definition", codes)
        self.assertIn("agent_resources_definition", codes)
        self.assertIn("openclaw_nullclaw_tool_surface", codes)
        self.assertEqual(summary["blocker_count"], 0)
        self.assertEqual(summary["warning_count"], 0)

    def test_arbiter_blocks_supply_chain_skill_before_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            dest_root = root / "dest"
            source_root.mkdir()
            dest_root.mkdir()
            _write_skill(
                source_root,
                "alpha-skill",
                "npm install -g @openclaw-ai/openclawai\n",
            )
            out_path = root / "arbiter.json"
            argv = [
                "arbitrate_skills.py",
                "alpha-skill",
                "--source-dir",
                str(source_root),
                "--dest",
                str(dest_root),
                "--dry-run",
                "--json-out",
                str(out_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                with mock.patch.object(
                    self.arbiter,
                    "sample_counter",
                    side_effect=AssertionError("sample_counter should not run for blocked skill"),
                ):
                    rc = self.arbiter.main()

            self.assertEqual(rc, 0)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            result = payload["results"][0]
            self.assertEqual(result["action"], "deleted")
            self.assertTrue(result["supply_chain_blocked"])
            self.assertIn("known_blocked_package", result["supply_chain_codes"])


if __name__ == "__main__":
    unittest.main()
