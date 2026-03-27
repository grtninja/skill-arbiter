from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest

from skill_arbiter.secret_hygiene import scan_repo


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)


class SecretHygieneTests(unittest.TestCase):
    def test_scan_repo_flags_real_github_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            sample = root / "README.md"
            sample.write_text(
                "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertFalse(result.passed)
            self.assertEqual(result.findings[0].kind, "github_token")

    def test_scan_repo_supports_diff_base_scanning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            sample = root / "README.md"
            sample.write_text("token=placeholder\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "safe baseline"], cwd=root, check=True, capture_output=True, text=True)
            sample.write_text("token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", "introduce secret"], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root, base_ref="HEAD^")

            self.assertFalse(result.passed)
            self.assertEqual(result.scope, "diff-files")
            self.assertEqual(result.findings[0].kind, "github_token")

    def test_scan_repo_ignores_placeholder_token_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            sample = root / "README.md"
            sample.write_text(
                "Use placeholder token ghp_EXAMPLEPLACEHOLDERTOKEN123456 in docs only.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
