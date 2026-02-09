from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import local_bridge_validate as validator  # noqa: E402


class LocalBridgeValidateTests(unittest.TestCase):
    def test_validation_passes_with_strict_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "src/service").mkdir(parents=True, exist_ok=True)
            (repo_root / "src/service/a.py").write_text("print('a')\n", encoding="utf-8")
            (repo_root / "src/service/b.py").write_text("print('b')\n", encoding="utf-8")

            payload = {
                "guidance_hints": [
                    {
                        "path": "src/service/a.py",
                        "finding": "Keep route contracts stable.",
                        "evidence": ["Function signature is public API."],
                        "confidence": 0.92,
                        "priority": "high",
                    },
                    {
                        "path": "src/service/b.py",
                        "finding": "Preserve response field ordering in serializer.",
                        "evidence": ["Downstream tests depend on key order."],
                        "confidence": 0.88,
                        "priority": "medium",
                    },
                ]
            }

            report = validator.validate_bridge_response(
                payload=payload,
                candidate_paths=["src/service/a.py", "src/service/b.py"],
                repo_root=repo_root,
                allowed_roots=[repo_root],
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["reason_codes"], [])
            self.assertEqual(report["hint_count"], 2)

    def test_unauthorized_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            payload = {
                "guidance_hints": [
                    {
                        "path": "../outside.txt",
                        "finding": "This should be rejected.",
                        "evidence": ["Path escapes repository root."],
                        "confidence": 0.9,
                    }
                ]
            }
            report = validator.validate_bridge_response(
                payload=payload,
                candidate_paths=["src/service/a.py"],
                repo_root=repo_root,
                allowed_roots=[repo_root],
            )
            self.assertEqual(report["status"], "validation_failed")
            self.assertIn("unauthorized_path", report["reason_codes"])

    def test_low_confidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            payload = {
                "guidance_hints": [
                    {
                        "path": "src/service/a.py",
                        "finding": "Weak signal.",
                        "evidence": ["Single uncertain marker."],
                        "confidence": 0.4,
                    },
                    {
                        "path": "src/service/b.py",
                        "finding": "Still weak.",
                        "evidence": ["Another low-quality marker."],
                        "confidence": 0.5,
                    },
                ]
            }
            report = validator.validate_bridge_response(
                payload=payload,
                candidate_paths=["src/service/a.py", "src/service/b.py"],
                repo_root=repo_root,
                allowed_roots=[repo_root],
            )
            self.assertEqual(report["status"], "validation_failed")
            self.assertIn("low_confidence", report["reason_codes"])

    def test_insufficient_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            payload = {
                "guidance_hints": [
                    {
                        "path": "src/service/a.py",
                        "finding": "One supported finding.",
                        "evidence": ["One citation only."],
                        "confidence": 0.9,
                    },
                    {
                        "path": "src/service/b.py",
                        "finding": "Missing evidence.",
                        "evidence": [],
                        "confidence": 0.9,
                    },
                ]
            }
            report = validator.validate_bridge_response(
                payload=payload,
                candidate_paths=["src/service/a.py", "src/service/b.py"],
                repo_root=repo_root,
                allowed_roots=[repo_root],
            )
            self.assertEqual(report["status"], "validation_failed")
            self.assertIn("insufficient_evidence", report["reason_codes"])

    def test_schema_invalid_for_empty_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            report = validator.validate_bridge_response(
                payload={},
                candidate_paths=["src/service/a.py"],
                repo_root=repo_root,
                allowed_roots=[repo_root],
            )
            self.assertEqual(report["status"], "validation_failed")
            self.assertIn("schema_invalid", report["reason_codes"])


if __name__ == "__main__":
    unittest.main()
