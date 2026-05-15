from __future__ import annotations

import importlib.util
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
        / "code-gap-sweeping"
        / "scripts"
        / "code_gap_sweep.py"
    )
    spec = importlib.util.spec_from_file_location("code_gap_sweep", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_repo_family_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root
        / "skill-candidates"
        / "code-gap-sweeping"
        / "scripts"
        / "repo_family_pipeline.py"
    )
    spec = importlib.util.spec_from_file_location("repo_family_pipeline", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CodeGapSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_parse_repo_pair_rejects_invalid_assignment(self) -> None:
        with self.assertRaises(ValueError):
            self.mod.parse_repo_pair("invalid-format")

    def test_parse_repo_pair_accepts_existing_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            name, path = self.mod.parse_repo_pair(f"demo={repo}")
            self.assertEqual(name, "demo")
            self.assertEqual(path, repo.resolve())

    def test_repo_family_pipeline_rejects_shell_unsafe_repo_names(self) -> None:
        mod = _load_repo_family_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()
            with self.assertRaises(ValueError):
                mod.parse_repo_pair(f"demo;touch-pwned={repo}")
            with self.assertRaises(ValueError):
                mod.parse_family_pair("demo$(touch pwned)=generic")

    def test_repo_family_pipeline_rejects_shell_unsafe_discovered_repo_names(self) -> None:
        mod = _load_repo_family_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = root / "demo;touch-pwned"
            unsafe.mkdir()
            (unsafe / ".git").mkdir()
            with self.assertRaises(ValueError):
                mod.discover_repos_under_root(root)

    def test_discover_repos_under_root_finds_immediate_git_children(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_a = root / "a"
            repo_b = root / "b"
            nested = root / "nested"
            repo_a.mkdir()
            repo_b.mkdir()
            nested.mkdir()
            (repo_a / ".git").mkdir()
            (repo_b / ".git").mkdir()
            (nested / "child").mkdir(parents=True)
            (nested / "child" / ".git").mkdir()

            found = self.mod.discover_repos_under_root(root)
            self.assertEqual(found, [("a", repo_a.resolve()), ("b", repo_b.resolve())])

    def test_analyze_repo_flags_release_hygiene_when_release_contract_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text("# changelog\n", encoding="utf-8")

            with mock.patch.object(
                self.mod,
                "changed_files",
                return_value=("deadbeef", ["src/service.py", "docs/README_INTERNAL.txt"]),
            ), mock.patch.object(self.mod, "todo_fixme_additions", return_value=[]):
                report = self.mod.analyze_repo(
                    "demo",
                    repo,
                    "main",
                    14,
                    self.mod.DIFF_MODE_COMMITTED,
                )

            categories = {item.category for item in report.findings}
            self.assertIn("release_hygiene_missing", categories)

    def test_analyze_repo_skips_release_hygiene_when_release_files_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text("# changelog\n", encoding="utf-8")

            with mock.patch.object(
                self.mod,
                "changed_files",
                return_value=("deadbeef", ["src/service.py", "pyproject.toml", "CHANGELOG.md"]),
            ), mock.patch.object(self.mod, "todo_fixme_additions", return_value=[]):
                report = self.mod.analyze_repo(
                    "demo",
                    repo,
                    "main",
                    14,
                    self.mod.DIFF_MODE_COMMITTED,
                )

            categories = {item.category for item in report.findings}
            self.assertNotIn("release_hygiene_missing", categories)

    def test_changed_files_working_tree_mode_includes_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()

            def fake_run_git(_repo_path: Path, args: list[str]) -> str:
                if args[:3] == ["merge-base", "HEAD", "main"]:
                    return "deadbeef\n"
                if args == ["diff", "--name-only", "deadbeef...HEAD"]:
                    return "src/committed.py\n"
                if args == ["diff", "--name-only", "HEAD"]:
                    return "src/working.py\n"
                if args == ["ls-files", "--others", "--exclude-standard"]:
                    return "src/new_file.py\n"
                raise AssertionError(f"unexpected git args: {args}")

            with mock.patch.object(self.mod, "resolve_base_ref", return_value="main"), mock.patch.object(
                self.mod,
                "run_git",
                side_effect=fake_run_git,
            ):
                merge_base, changed = self.mod.changed_files(
                    repo,
                    base_ref="main",
                    since_days=14,
                    diff_mode=self.mod.DIFF_MODE_WORKING_TREE,
                )

            self.assertEqual(merge_base, "deadbeef")
            self.assertEqual(changed, ["src/new_file.py", "src/working.py"])

    def test_todo_fixme_additions_combined_includes_patch_and_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            note = repo / "notes.md"
            note.write_text("- [ ] TODO follow-up with docs\n", encoding="utf-8")

            patch_text = "\n".join(
                [
                    "diff --git a/src/service.py b/src/service.py",
                    "+++ b/src/service.py",
                    "+// TODO add retry limit",
                    "+print('no marker TODO')",
                ]
            )

            with mock.patch.object(self.mod, "collect_patch_text", return_value=patch_text), mock.patch.object(
                self.mod,
                "run_git",
                return_value="notes.md\n",
            ):
                evidence = self.mod.todo_fixme_additions(
                    repo,
                    merge_base="deadbeef",
                    diff_mode=self.mod.DIFF_MODE_COMBINED,
                )

            self.assertIn("src/service.py: +// TODO add retry limit", evidence)
            self.assertIn("notes.md: +- [ ] TODO follow-up with docs", evidence)
            self.assertEqual(len(evidence), 2)

    def test_run_git_decodes_non_utf8_output_with_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            completed = self.mod.subprocess.CompletedProcess(
                args=["git"],
                returncode=0,
                stdout=b"src/file.py\nbad-\x9d-byte\n",
                stderr=b"",
            )
            with mock.patch.object(self.mod.subprocess, "run", return_value=completed):
                output = self.mod.run_git(repo, ["status"])
            self.assertIn("src/file.py", output)
            self.assertIn("bad-�-byte", output)


if __name__ == "__main__":
    unittest.main()
