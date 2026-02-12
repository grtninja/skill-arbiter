from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root
        / "skill-candidates"
        / "repo-b-comfy-amuse-capcut-pipeline"
        / "scripts"
        / "comfy_media_pipeline_check.py"
    )
    spec = importlib.util.spec_from_file_location("comfy_media_pipeline_check", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module at {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class ComfyMediaPipelineCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_module()

    def test_fetch_json_rejects_non_object_payload(self) -> None:
        with mock.patch.object(
            self.mod.urllib.request,
            "urlopen",
            return_value=_FakeResponse(200, ["not-an-object"]),
        ):
            ok, status, payload, error = self.mod.fetch_json("http://127.0.0.1:9000", "/x", 1.0)
        self.assertFalse(ok)
        self.assertEqual(status, 200)
        self.assertEqual(payload, {})
        self.assertIn("not an object", error)

    def test_main_fails_when_required_profile_and_amuse_missing(self) -> None:
        args = argparse.Namespace(
            base_url="http://127.0.0.1:9000",
            require_profile=["video-edit"],
            require_capcut=True,
            require_amuse=True,
            timeout_seconds=1.0,
            json_out="",
        )
        with mock.patch.object(self.mod, "parse_args", return_value=args), mock.patch.object(
            self.mod,
            "fetch_json",
            side_effect=[
                (
                    True,
                    200,
                    {
                        "enabled": True,
                        "running": True,
                        "tools": ["shim.comfy.workflow.submit", "shim.comfy.pipeline.run"],
                        "resources": ["shim.comfy.status", "shim.comfy.queue", "shim.comfy.history"],
                    },
                    "",
                ),
                (
                    True,
                    200,
                    {"default_profile": "default", "profiles": [{"profile": "default"}]},
                    "",
                ),
                (True, 200, {"enabled": False, "reachable": False}, ""),
            ],
        ):
            with mock.patch("sys.stdout", new=io.StringIO()):
                rc = self.mod.main()
        self.assertEqual(rc, 1)

    def test_main_passes_when_required_contracts_exist(self) -> None:
        args = argparse.Namespace(
            base_url="http://127.0.0.1:9000",
            require_profile=["video-edit"],
            require_capcut=True,
            require_amuse=True,
            timeout_seconds=1.0,
            json_out="",
        )
        with mock.patch.object(self.mod, "parse_args", return_value=args), mock.patch.object(
            self.mod,
            "fetch_json",
            side_effect=[
                (
                    True,
                    200,
                    {
                        "enabled": True,
                        "running": True,
                        "tools": ["shim.comfy.workflow.submit", "shim.comfy.pipeline.run"],
                        "resources": ["shim.comfy.status", "shim.comfy.queue", "shim.comfy.history"],
                    },
                    "",
                ),
                (
                    True,
                    200,
                    {
                        "default_profile": "video-edit",
                        "profiles": [
                            {
                                "profile": "video-edit",
                                "capcut_export": {"editor": "capcut"},
                            }
                        ],
                    },
                    "",
                ),
                (True, 200, {"enabled": True, "reachable": True}, ""),
            ],
        ):
            with mock.patch("sys.stdout", new=io.StringIO()):
                rc = self.mod.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
