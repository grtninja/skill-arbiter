from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from skill_arbiter.public_readiness import run_public_readiness_scan


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
            "Windows-first NullClaw host security app for local skill governance and guarded remediation.",
            "## For humans",
            "## For AI agents",
            "## Local advisor",
            "Works with loopback-hosted OpenAI-compatible coding-model surfaces.",
            "## Public support",
            "https://github.com/grtninja/skill-arbiter",
            "https://www.patreon.com/cw/grtninja",
            "## Public release readiness",
            "## Safety and abuse handling",
            "## Quick start",
            "Launch through the shell-free Windows launcher.",
        ]))
        for rel in [
            "AGENTS.md",
            "BOUNDARIES.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SKILL.md",
            "skill-catalog.md",
            "docs/PROJECT_SCOPE.md",
            "docs/SCOPE_TRACKER.md",
            "references/skill-catalog.md",
            "references/skill-vetting-report.md",
            "scripts/launch_security_console.vbs",
            "scripts/install_security_console_shortcut.ps1",
            "INSTRUCTIONS.md",
        ]:
            if rel == "AGENTS.md":
                _write(root / rel, "\n".join([
                    "G:\\GitHub is the canonical repo root.",
                    "Public authority plane: http://127.0.0.1:9000/v1",
                    "Hosted lane: http://127.0.0.1:2337/v1",
                    "Continue local-agent surfaces keep visible action-state parity.",
                    "LM Studio is an operator surface, not an authority source.",
                    "No-stop doctrine, minimum runtime law, trusted folders, local-subagent state, reasoning visibility, and patience runtime window apply.",
                    "skill-hub request-loopback-resume skill-common-sense-engineering usage-watcher skill-cost-credit-governor skill-trust-ledger",
                    "no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows",
                ]))
            elif rel == "BOUNDARIES.md":
                _write(root / rel, "\n".join([
                    "G:\\GitHub remains canonical.",
                    "Public authority plane: http://127.0.0.1:9000/v1",
                    "Hosted lane: http://127.0.0.1:2337/v1",
                    "Continue-facing local-agent surfaces keep visible action-state parity.",
                    "No-stop doctrine and Minimum runtime law apply.",
                    "Trusted folders, local-subagent state, reasoning visibility, and patience runtime window remain required.",
                    "skill-hub request-loopback-resume skill-common-sense-engineering usage-watcher skill-cost-credit-governor skill-trust-ledger",
                ]))
            elif rel == "INSTRUCTIONS.md":
                _write(root / rel, "\n".join([
                    "The real local governance console stays authoritative.",
                    "Continue-facing lanes keep the current contract visible.",
                    "Continue-facing local-agent lanes keep visible action-state parity.",
                    "No-stop doctrine and minimum runtime law apply.",
                    "Trusted folders, local-subagent state, reasoning visibility, and patience runtime window remain required.",
                    "skill-hub request-loopback-resume skill-common-sense-engineering usage-watcher skill-cost-credit-governor skill-trust-ledger",
                ]))
            elif rel == "CONTRIBUTING.md":
                _write(root / rel, "\n".join([
                    "Contributors must preserve the no-stop doctrine and minimum runtime law.",
                    "Continue local-agent lanes keep visible action-state parity.",
                    "Avoid browser-tool or headless fallback surfaces as the primary contract.",
                    "Trusted folders, local-subagent state, reasoning visibility, and patience runtime window remain required.",
                    "skill-hub request-loopback-resume skill-common-sense-engineering usage-watcher skill-cost-credit-governor skill-trust-ledger",
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
            elif rel == "skill-catalog.md":
                _write(root / rel, "\n".join([
                    "# skill-arbiter Skill Catalog",
                    "Canonical discovery surface for humans and crawlers.",
                ]))
            else:
                _write(root / rel, "ok\n")
        _write(root / "skill_arbiter" / "collaboration_support.py", "DEFAULT_TRUST_LEDGER = {}\ntrust_ledger = DEFAULT_TRUST_LEDGER\nledger = trust_ledger\n# trust ledger\n")
        _write(root / "references" / "codex-config-self-maintenance.md", "candidate-first validation\ntrusted folders\nlocal-subagent\nrequired local-agent doctrine\n<CODEX_CONFIG_PATH>\nprofiles.json\n")
        bundle = root / "skill-candidates" / "codex-config-self-maintenance"
        _write(bundle / "SKILL.md", "candidate-first validation\ntrusted folders\nlocal-subagent\nrequired local-agent doctrine\n<CODEX_CONFIG_PATH>\nprofiles.json\n")
        _write(bundle / "references" / "config-contract.md", "candidate-first validation\ntrusted folders\nlocal-subagent\nrequired local-agent doctrine\n<CODEX_CONFIG_PATH>\nprofiles.json\n")
        _write(bundle / "references" / "manifest-evidence.md", "candidate-first validation\ntrusted folders\nlocal-subagent\nrequired local-agent doctrine\n<CODEX_CONFIG_PATH>\nprofiles.json\n")
        _write(bundle / "scripts" / "validate_candidate.py", "print('ok')\n")
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

    def test_public_readiness_flags_stale_continue_browser_headless_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "README.md",
                "\n".join(
                    [
                        "# skill-arbiter",
                        "Continue should use browser tools and headless fallback behavior here.",
                        "## Public support",
                        "https://github.com/grtninja/skill-arbiter",
                        "https://www.patreon.com/cw/grtninja",
                        "## Public release readiness",
                        "## Safety and abuse handling",
                        "Hosted lane: http://127.0.0.1:2337/v1",
                        "LM Studio remains an operator surface.",
                        "No empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.",
                    ]
                ),
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("stale_continue_browser_headless", codes)

    def test_public_readiness_requires_no_stop_and_minimum_runtime_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "README.md", "# skill-arbiter\n## Public support\nhttps://github.com/grtninja/skill-arbiter\nhttps://www.patreon.com/cw/grtninja\n## Public release readiness\n## Safety and abuse handling\nHosted lane: http://127.0.0.1:2337/v1\nLM Studio remains an operator surface.\nNo empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.\n")
            _write(root / "BOUNDARIES.md", "# boundary\n")
            _write(root / "INSTRUCTIONS.md", "# instructions\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("meta_harness_doc_contract_incomplete", codes)

    def test_public_readiness_flags_missing_no_stop_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "README.md", "# skill-arbiter\n## Public support\nhttps://github.com/grtninja/skill-arbiter\nhttps://www.patreon.com/cw/grtninja\n## Public release readiness\n## Safety and abuse handling\nHosted lane: http://127.0.0.1:2337/v1\nLM Studio remains an operator surface.\nNo empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.\n")
            _write(root / "INSTRUCTIONS.md", "ok\n")
            _write(root / "BOUNDARIES.md", "ok\n")
            _write(root / "CONTRIBUTING.md", "ok\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("no_stop_minimum_runtime_contract_incomplete", codes)

    def test_public_readiness_flags_missing_debt_ledger_proof_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "skill_arbiter" / "collaboration_support.py", "ledger = None\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("debt_ledger_proof_contract_incomplete", codes)

    def test_public_readiness_flags_missing_local_agent_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "README.md", "# skill-arbiter\n## Public support\nhttps://github.com/grtninja/skill-arbiter\nhttps://www.patreon.com/cw/grtninja\n## Public release readiness\n## Safety and abuse handling\nHosted lane: http://127.0.0.1:2337/v1\nLM Studio remains an operator surface.\nNo empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.\n")
            _write(root / "BOUNDARIES.md", "# boundary\n")
            _write(root / "INSTRUCTIONS.md", "# instructions\n")
            _write(root / "CONTRIBUTING.md", "# contributing\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("local_agent_contract_incomplete", codes)

    def test_public_readiness_flags_missing_reasoning_visibility_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(root / "README.md", "# skill-arbiter\n## Public support\nhttps://github.com/grtninja/skill-arbiter\nhttps://www.patreon.com/cw/grtninja\n## Public release readiness\n## Safety and abuse handling\nHosted lane: http://127.0.0.1:2337/v1\nLM Studio remains an operator surface.\nNo empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.\n")
            _write(root / "BOUNDARIES.md", "# boundary\n")
            _write(root / "INSTRUCTIONS.md", "# instructions\n")
            _write(root / "CONTRIBUTING.md", "# contributing\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("reasoning_visibility_contract_incomplete", codes)

    def test_public_readiness_flags_browser_first_continue_or_copilot_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "README.md",
                "\n".join(
                    [
                        "# skill-arbiter",
                        "Continue should use browser tools first.",
                        "Copilot should use headless fallback behavior.",
                        "## Public support",
                        "https://github.com/grtninja/skill-arbiter",
                        "https://www.patreon.com/cw/grtninja",
                        "## Public release readiness",
                        "## Safety and abuse handling",
                        "Hosted lane: http://127.0.0.1:2337/v1",
                        "LM Studio remains an operator surface.",
                        "No empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.",
                    ]
                ),
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("continue_copilot_browser_first_contract", codes)

    def test_public_readiness_flags_stale_self_diagnosis_lane_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "README.md",
                "\n".join(
                    [
                        "# skill-arbiter",
                        "Continue is in degraded mode and waiting for a trigger.",
                        "Copilot should ask for a file path first.",
                        "## Public support",
                        "https://github.com/grtninja/skill-arbiter",
                        "https://www.patreon.com/cw/grtninja",
                        "## Public release readiness",
                        "## Safety and abuse handling",
                        "Hosted lane: http://127.0.0.1:2337/v1",
                        "LM Studio remains an operator surface.",
                        "No empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows are accepted.",
                    ]
                ),
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("continue_copilot_stale_self_diagnosis_contract", codes)

    def test_public_readiness_flags_missing_mandatory_skill_chain_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "AGENTS.md",
                "\n".join(
                    [
                        "G:\\GitHub is the canonical repo root.",
                        "Public authority plane: http://127.0.0.1:9000/v1",
                        "Hosted lane: http://127.0.0.1:2337/v1",
                        "Continue local-agent surfaces keep visible action-state parity.",
                        "LM Studio is an operator surface, not an authority source.",
                        "No-stop doctrine, minimum runtime law, trusted folders, local-subagent state, reasoning visibility, and patience runtime window apply.",
                        "no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows",
                    ]
                ),
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("mandatory_skill_chain_contract_incomplete", codes)

    def test_public_readiness_flags_incomplete_codex_config_skill_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            bundle = root / "skill-candidates" / "codex-config-self-maintenance"
            _write(
                bundle / "SKILL.md",
                "\n".join(
                    [
                        "---",
                        "name: codex-config-self-maintenance",
                        "description: maintain Codex config.toml safely",
                        "---",
                        "",
                        "Use this skill to keep Codex configuration changes safe.",
                    ]
                ),
            )
            _write(root / "references" / "codex-config-self-maintenance.md", "reference only\n")
            _write(bundle / "references" / "config-contract.md", "contract only\n")
            _write(bundle / "references" / "manifest-evidence.md", "evidence only\n")
            _write(bundle / "scripts" / "validate_candidate.py", "print('ok')\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("codex_config_skill_bundle_incomplete", codes)

    def test_public_readiness_flags_missing_codex_parity_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            _write(
                root / "AGENTS.md",
                "\n".join(
                    [
                        "G:\\GitHub is the canonical repo root.",
                        "Public authority plane: http://127.0.0.1:9000/v1",
                        "Hosted lane: http://127.0.0.1:2337/v1",
                        "Continue local-agent surfaces keep visible action-state parity.",
                        "LM Studio is an operator surface, not an authority source.",
                        "No-stop doctrine and minimum runtime law apply.",
                        "skill-hub request-loopback-resume skill-common-sense-engineering usage-watcher skill-cost-credit-governor skill-trust-ledger",
                        "no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows",
                    ]
                ),
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("codex_parity_contract_incomplete", codes)

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

    def test_public_readiness_blocks_local_private_mode_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_repo(root)
            self._populate_core_files(root)
            private_file = root / "skill_arbiter" / "private" / "sealed_extension" / "contracts.py"
            private_file.parent.mkdir(parents=True, exist_ok=True)
            private_file.write_text("TOP_SECRET_LOCAL_ONLY = True\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_public_readiness_scan(root)
            codes = {item["code"] for item in payload["findings"]}

            self.assertFalse(payload["passed"])
            self.assertIn("privacy_local-only-private-surface", codes)


if __name__ == "__main__":
    unittest.main()
