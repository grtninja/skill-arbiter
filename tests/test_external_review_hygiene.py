from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import unittest

from skill_arbiter.external_review_hygiene import scan_repo


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)


class ExternalReviewHygieneTests(unittest.TestCase):
    def test_scan_repo_flags_vendor_markers_in_skill_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            skill = root / "skill-candidates" / "sample" / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text("Use tesslio skill-review here.\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertFalse(result.passed)
            self.assertEqual(result.findings[0].kind, "vendor_name")

    def test_scan_repo_flags_remote_workflow_uses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            workflow = root / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text(
                "jobs:\n"
                "  scan:\n"
                "    steps:\n"
                "      - uses: tesslio/skill-review-and-optimize@v1\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertFalse(result.passed)
            self.assertTrue(any(item.kind == "non_local_workflow_uses" for item in result.findings))

    def test_scan_repo_ignores_policy_docs_outside_governed_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root)
            readme = root / "README.md"
            readme.write_text("Do not add tesslio tooling here.\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)

            result = scan_repo(root)

            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
