from __future__ import annotations

import unittest

from scripts.generate_skillhub_alignment import SkillHubSelection, _score_decision


class SkillHubAlignmentTests(unittest.TestCase):
    def test_repo_owned_rewrite_only_always_stays_rewrite_candidate(self) -> None:
        selection = SkillHubSelection(
            name="monitoring-expert",
            github_owner="Jeffallan",
            github_repo="claude-skills",
            mode="rewrite_only",
            mapping="rewrite-only inspiration",
            target_gap="media-workbench-indexing-governance",
            decision_hint="rewrite_candidate",
        )
        decision, reasons = _score_decision(selection, None, None, set())
        self.assertEqual(decision, "rewrite_candidate")
        self.assertIn("rewrite-only", reasons[0])

    def test_existing_local_name_is_ignored_as_overlap(self) -> None:
        selection = SkillHubSelection(
            name="review-pr",
            github_owner="openclaw",
            github_repo="openclaw",
            mode="direct_vet",
            mapping="overlap check",
            target_gap="media-workbench-worker-contracts",
            decision_hint="import_candidate",
        )
        decision, reasons = _score_decision(selection, None, None, {"review-pr"})
        self.assertEqual(decision, "ignore_overlap")
        self.assertIn("already covered", reasons[0])
