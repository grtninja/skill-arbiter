from __future__ import annotations

import unittest

from skill_arbiter.skill_game_runtime import original_skill_levels, status_payload


class SkillGameRuntimeTests(unittest.TestCase):
    def test_original_skill_levels_are_loaded_from_progression_reference(self) -> None:
        levels = original_skill_levels()
        self.assertGreater(len(levels), 0)
        skill_arbiter_row = next((row for row in levels if row["name"] == "skill-arbiter"), None)
        self.assertIsNotNone(skill_arbiter_row)
        self.assertEqual(skill_arbiter_row["level"], 9)

    def test_status_payload_reports_original_skill_levels(self) -> None:
        payload = status_payload({"skills": [], "skill_count": 0, "incident_count": 0})
        self.assertIn("original_skill_levels", payload)
        self.assertIn("original_skill_count", payload)
        self.assertGreater(payload["original_skill_count"], 0)


if __name__ == "__main__":
    unittest.main()
