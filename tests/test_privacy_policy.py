from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest

from skill_arbiter.privacy_policy import scan_repo
from skill_arbiter.self_governance import run_self_governance_scan


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)


class PrivacyPolicyTests(unittest.TestCase):
    def test_scan_repo_flags_private_paths_and_repo_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            repo_name = "Falcon" + "-Sandbox"
            drive_root = "C:/" + "Users/"
            user_name = "Test" + "User"
            abs_repo_path = f"{drive_root}{user_name}/Documents/GitHub/{repo_name}"
            skill_dir = root / "skill-candidates" / "demo-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: demo-skill",
                        f"description: Diagnose behavior in {repo_name}.",
                        "---",
                        "",
                        f"Run from `{repo_name}` root:",
                        f'Open "{abs_repo_path}".',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertFalse(result.passed)
            kinds = {item.kind for item in result.findings}
            self.assertIn("private-repo-identifier", kinds)
            self.assertIn("user-absolute-path", kinds)
            self.assertIn("repo-placeholder-required", kinds)

    def test_self_governance_scan_flags_browser_launch_and_hidden_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            scripts_dir = root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            (scripts_dir / "bad_launch.py").write_text(
                "\n".join(
                    [
                        "import subprocess",
                        "import webbrowser",
                        "webbrowser.open('https://example.com')",
                        "subprocess.Popen(['python', 'worker.py'], creationflags=subprocess.CREATE_NO_WINDOW)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            payload = run_self_governance_scan(root)

            self.assertFalse(payload["passed"])
            codes = {item["code"] for item in payload["findings"]}
            self.assertIn("browser_autolaunch", codes)
            self.assertIn("hidden_process_launch", codes)


if __name__ == "__main__":
    unittest.main()
