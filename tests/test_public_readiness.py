from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from skill_arbiter.public_readiness import (
    _public_shape_guard_term_hits,
    _publish_guard_terms,
    run_public_readiness_scan,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PublicReadinessTests(unittest.TestCase):
    def _init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)

    def _populate_core_files(self, root: Path, *, include_runtime_ignore: bool = True) -> None:
        _write(root / "README.md", "\n".join([
            "# skill-arbiter",
            "## Public support",
            "https://github.com/grtninja/skill-arbiter",
            "https://www.patreon.com/cw/grtninja",
            "## Public release readiness",
            "## Safety and abuse handling",
            "Hosted lane: http://127.0.0.1:2337/v1",
            "LM Studio remains an operator surface.",
            "No empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.",
        ]))
        for rel in [
            "AGENTS.md",
            "BOUNDARIES.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SKILL.md",
            "docs/PROJECT_SCOPE.md",
            "docs/SCOPE_TRACKER.md",
            "references/skill-catalog.md",
            "references/skill-vetting-report.md",
            "scripts/launch_security_console.vbs",
            "scripts/install_security_console_shortcut.ps1",
        ]:
            if rel == "AGENTS.md":
                _write(root / rel, "\n".join([
                    "Hosted lane: http://127.0.0.1:2337/v1",
                    "LM Studio is an operator surface, not an authority source.",
                    "no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows",
                ]))
            elif rel == "references/skill-catalog.md":
                _write(root / rel, "\n".join([
                    "# NullClaw Skill Catalog",
                    "## Advisor Note",
                    "",
                    "_Live local advisor note omitted from public-shape catalog._",
                    "",
                    "## Interop Surfaces",
                ]))
            else:
                _write(root / rel, "ok\n")
        _write(root / "scripts/nullclaw_agent.py", "print('ok')\n")
        _write(root / "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.png", "png\n")
        _write(root / "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.ico", "ico\n")
        if include_runtime_ignore:
            _write(root / ".gitignore", "apps/nullclaw-desktop/runtime/\n.codex-index/\n")
        else:
            _write(root / ".gitignore", "__pycache__/\n")

    def test_public_readiness_passes_for_sanitized_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)

            self.assertTrue(payload["passed"])
            self.assertEqual(payload["critical_count"], 0)
            self.assertEqual(payload["high_count"], 0)

    def test_public_readiness_flags_tracked_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root, include_runtime_ignore=False)
            _write(root / "apps/nullclaw-desktop/runtime/session.json", "{}\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("tracked_runtime_dir", codes)

    def test_public_readiness_flags_model_route_authority_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "AGENTS.md", "Direct LM Studio: http://127.0.0.1:1234/v1. Hosted lane: http://127.0.0.1:2337/v1.\n9000/v1 is canonical authority.\n")
            _write(root / "INSTRUCTIONS.md", "9000/v1 is canonical authority.\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("model_route_contract_incomplete", codes)
            self.assertIn("model_route_authority_conflict", codes)

    def test_public_readiness_flags_shell_wrapped_launch_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "CONTRIBUTING.md",
                "Launch with:\n"
                "powershell -ExecutionPolicy Bypass -File .\\scripts\\start_security_console.ps1\n",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("shell_wrapped_desktop_launch_docs", codes)

    def test_public_readiness_flags_candidate_meta_harness_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "skill-candidates" / "local-compute-usage" / "SKILL.md",
                "\n".join(
                    [
                        "---",
                        "name: local-compute-usage",
                        "description: local",
                        "---",
                        "",
                        '$env:REPO_B_CONTINUE_ALLOWED_ROOTS = "$env:USERPROFILE\\Documents\\GitHub\\<PRIVATE_REPO_B>"',
                    ]
                ),
            )
            _write(
                root / "skill-candidates" / "local-compute-usage" / "agents" / "openai.yaml",
                "interface:\n  display_name: demo\n  short_description: demo\n  default_prompt: demo\n",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertFalse(payload["checks"]["candidate_meta_harness"])
            self.assertIn("candidate_legacy_repo_root_alias", codes)

    def test_public_readiness_flags_legacy_repo_root_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "skill-candidates" / "demo" / "SKILL.md", "$env:USERPROFILE\\Documents\\GitHub\\demo\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("candidate_legacy_repo_root_alias", codes)

    def test_public_readiness_flags_untracked_publish_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            _write(root / "skill_arbiter" / "meta_harness_policy.py", "SCAN = True\n")

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertFalse(payload["checks"]["tracked_publish_surface"])
            self.assertIn("untracked_publish_surface", codes)

    def test_guard_terms_fall_back_to_public_safe_list(self) -> None:
        # Neither the private nor the public guard-term file exists; the gate
        # must fall back to the public-safe built-in list instead of silently
        # passing with zero terms. (Muse)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            terms = _publish_guard_terms(root)
            self.assertTrue(terms)
            self.assertIn("c:\\users\\", terms)
            self.assertIn("hotmail.com", terms)  # guard-vocabulary-ok

    def test_guard_terms_prefer_private_file_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "skill_arbiter" / "private" / "publish_guard_terms.txt",
                    "super-secret-internal-term\n")
            terms = _publish_guard_terms(root)
            self.assertIn("super-secret-internal-term", terms)
            self.assertIn("c:\\users\\", terms)  # built-in list always applies

    def test_guard_term_hit_flags_tracked_private_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            _write(root / "docs" / "notes.md",
                    "installed under c:\\users\\someone\\documents\\github\\skill-arbiter\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            hits = _public_shape_guard_term_hits(root)
            self.assertTrue(any(hit.startswith("docs/notes.md:") for hit in hits))

    def test_guard_definition_files_are_exempt(self) -> None:
        # The vocabulary-definition files must not flag their own
        # declarations. (Muse)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            _write(root / "skill_arbiter" / "public_readiness.py",
                    'TERMS = ("hotmail.com",)  # guard-vocabulary-ok\n')
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            hits = _public_shape_guard_term_hits(root)
            self.assertFalse(any(hit.startswith("skill_arbiter/public_readiness.py:") for hit in hits))

    def test_guard_definition_files_still_catch_real_leaks(self) -> None:
        # Narrowed exemption: a real leak added elsewhere in a definition
        # file must be caught, not skipped with the whole file. (Muse)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            _write(root / "skill_arbiter" / "public_readiness.py",  # guard-vocabulary-ok
                    'PUBLIC_SAFE_GUARD_TERMS = (\n    "hotmail.com",\n)\n'  # guard-vocabulary-ok
                    '# operator contact: alice@hotmail.com\n')  # guard-vocabulary-ok
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            hits = _public_shape_guard_term_hits(root)
            self.assertTrue(any(hit.startswith("skill_arbiter/public_readiness.py:") for hit in hits))


if __name__ == "__main__":
    unittest.main()
