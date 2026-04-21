from __future__ import annotations

import importlib.util
from types import SimpleNamespace
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "generate_skill_catalog.py"
    spec = importlib.util.spec_from_file_location("generate_skill_catalog", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateSkillCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_main_writes_root_and_reference_catalogs(self) -> None:
        payload = {
            "generated_at": "2026-04-21T12:00:00Z",
            "skills": [],
            "sources": [],
            "incidents": [],
            "recent_work_skills": [],
            "legitimacy_summary": {},
            "interop_sources": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "references").mkdir(parents=True, exist_ok=True)
            (repo_root / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        'name: "skill-arbiter"',
                        'author: "grtninja"',
                        'canonical_source: "https://github.com/grtninja/skill-arbiter"',
                        'description: "root skill"',
                        "---",
                        "",
                        "# Root",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            skill_dir = repo_root / "skill-candidates" / "white-hat"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        'name: "white-hat"',
                        'author: "grtninja"',
                        'canonical_source: "https://github.com/grtninja/skill-arbiter"',
                        'description: "defender-first checks"',
                        "---",
                        "",
                        "# White Hat",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            third_party_dir = repo_root / "skill-candidates" / "gh-issues"
            third_party_dir.mkdir(parents=True, exist_ok=True)
            (third_party_dir / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        'name: "gh-issues"',
                        'description: "Contains a noisy external channel id -1002381931352"',
                        "---",
                        "",
                        "# GitHub Issues",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            fake_ls_files = "\n".join(
                [
                    "SKILL.md",
                    "skill-candidates/gh-issues/SKILL.md",
                    "skill-candidates/white-hat/SKILL.md",
                    "",
                ]
            )

            with (
                mock.patch.object(self.mod, "REPO_ROOT", repo_root),
                mock.patch.object(self.mod, "build_inventory_snapshot", return_value=payload),
                mock.patch.object(
                    self.mod.subprocess,
                    "run",
                    return_value=SimpleNamespace(returncode=0, stdout=fake_ls_files),
                ),
            ):
                rc = self.mod.main()

            self.assertEqual(rc, 0)
            root_catalog = (repo_root / "skill-catalog.md").read_text(encoding="utf-8")
            ref_catalog = (repo_root / "references" / "skill-catalog.md").read_text(encoding="utf-8")
            self.assertIn("# skill-arbiter Skill Catalog", root_catalog)
            self.assertIn("https://github.com/grtninja/skill-arbiter", root_catalog)
            self.assertIn("`skill-candidates/white-hat/SKILL.md`", root_catalog)
            self.assertIn("Rows without explicit provenance metadata stay blank", root_catalog)
            self.assertIn("| `gh-issues` | `skill_candidate` | - | - | - | `skill-candidates/gh-issues/SKILL.md` |", root_catalog)
            self.assertIn("# NullClaw Skill Catalog", ref_catalog)

    def test_repo_skill_paths_fails_closed_when_git_listing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with mock.patch.object(
                self.mod.subprocess,
                "run",
                return_value=SimpleNamespace(returncode=1, stdout="", stderr="fatal: not a git repository"),
            ):
                with self.assertRaisesRegex(RuntimeError, "refusing to scan untracked skills"):
                    self.mod._repo_skill_paths(repo_root)


if __name__ == "__main__":
    unittest.main()
