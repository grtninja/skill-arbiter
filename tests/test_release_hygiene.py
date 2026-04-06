from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "check_release_hygiene.py"
    spec = importlib.util.spec_from_file_location("check_release_hygiene", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_collect_changed_files_includes_working_tree_and_untracked(self) -> None:
        def fake_run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
            payload = {
                ("git", "merge-base", "HEAD", "main"): "deadbeef\n",
                ("git", "diff", "--name-only", "deadbeef...HEAD"): "README.md\n",
                ("git", "diff", "--name-only"): "skill_arbiter/public_readiness.py\n",
                ("git", "diff", "--cached", "--name-only"): ".github/pull_request_template.md\n",
                ("git", "ls-files", "--others", "--exclude-standard"): "skill_arbiter/meta_harness_policy.py\n",
            }
            return subprocess.CompletedProcess(cmd, 0, payload.get(tuple(cmd), ""), "")

        with mock.patch.object(self.mod, "run", side_effect=fake_run):
            merge_base, changed = self.mod.collect_changed_files("main")

        self.assertEqual(merge_base, "deadbeef")
        self.assertEqual(
            changed,
            [
                ".github/pull_request_template.md",
                "README.md",
                "skill_arbiter/meta_harness_policy.py",
                "skill_arbiter/public_readiness.py",
            ],
        )

    def test_main_fails_for_release_impacting_worktree_changes_without_release_update(self) -> None:
        with mock.patch.object(self.mod, "parse_args", return_value=Namespace(base_ref="main")):
            with mock.patch.object(self.mod, "resolve_base_ref", return_value="main"):
                with mock.patch.object(
                    self.mod,
                    "collect_changed_files",
                    return_value=("deadbeef", ["skill_arbiter/public_readiness.py"]),
                ):
                    with mock.patch.object(self.mod, "parse_current_semver", return_value=(0, 2, 23)):
                        with mock.patch.object(self.mod, "parse_base_semver", return_value=(0, 2, 23)):
                            with mock.patch.object(self.mod, "parse_latest_changelog_version", return_value="0.2.23"):
                                rc = self.mod.main()

        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
