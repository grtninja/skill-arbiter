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
            "## Public support",
            "https://github.com/grtninja/skill-arbiter",
            "https://www.patreon.com/cw/grtninja",
            "## Public release readiness",
            "## Safety and abuse handling",
        ]))
        for rel in [
            "BOUNDARIES.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "SKILL.md",
            "docs/PROJECT_SCOPE.md",
            "docs/SCOPE_TRACKER.md",
            "references/skill-vetting-report.md",
            "scripts/install_security_console_shortcut.ps1",
        ]:
            _write(root / rel, "ok\n")
        _write(root / "scripts/nullclaw_agent.py", "print('ok')\n")
        _write(root / "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.png", "png\n")
        _write(root / "apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.ico", "ico\n")
        if include_runtime_ignore:
            _write(root / ".gitignore", "apps/nullclaw-desktop/runtime/\n")
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


if __name__ == "__main__":
    unittest.main()
