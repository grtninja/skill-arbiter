#!/usr/bin/env python3
"""Shared local path defaults for the local-comfy-wan-multigpu scripts."""

from __future__ import annotations

import os
from pathlib import Path


def _env_path(name: str, fallback: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return fallback
    return Path(raw).expanduser()


HOME = Path.home()
LOCAL_MEDIA_ROOT = _env_path(
    "LOCAL_MEDIA_WORKBENCH_ROOT",
    HOME / "Documents" / "Local-Media-Workbench",
)
DEFAULT_WORK_ITEMS = _env_path(
    "LOCAL_MEDIA_WORK_ITEMS_ROOT",
    LOCAL_MEDIA_ROOT / "evidence" / "work_items",
)
DEFAULT_WORKBENCH_TOOLS = _env_path(
    "LOCAL_MEDIA_WORKBENCH_TOOLS_ROOT",
    LOCAL_MEDIA_ROOT / "tools",
)
DEFAULT_KOKORO_MODEL = _env_path(
    "LOCAL_KOKORO_MODEL_PATH",
    LOCAL_MEDIA_ROOT / "models" / "kokoro-v1.0.onnx",
)
DEFAULT_KOKORO_VOICES = _env_path(
    "LOCAL_KOKORO_VOICES_PATH",
    LOCAL_MEDIA_ROOT / "models" / "voices-v1.0.bin",
)
DEFAULT_MUSETALK_REPO = _env_path(
    "LOCAL_MUSETALK_REPO",
    HOME / "tools" / "MuseTalk",
)
DEFAULT_COMFY_BASE = _env_path(
    "LOCAL_COMFY_BASE_DIR",
    HOME / "Documents" / "ComfyUI",
)
DEFAULT_COMFY_USER = _env_path("LOCAL_COMFY_USER_DIR", DEFAULT_COMFY_BASE / "user")
DEFAULT_COMFY_INPUT = _env_path("LOCAL_COMFY_INPUT_DIR", DEFAULT_COMFY_BASE / "input")
DEFAULT_COMFY_OUTPUT = _env_path("LOCAL_COMFY_OUTPUT_DIR", DEFAULT_COMFY_BASE / "output")
DEFAULT_COMFY_PYTHON = _env_path(
    "LOCAL_COMFY_PYTHON",
    DEFAULT_COMFY_BASE / ".venv" / "Scripts" / "python.exe",
)
DEFAULT_COMFY_MAIN = _env_path(
    "LOCAL_COMFY_MAIN_PATH",
    DEFAULT_COMFY_BASE / "main.py",
)
DEFAULT_COMFY_FRONTEND = _env_path(
    "LOCAL_COMFY_FRONTEND_DIR",
    DEFAULT_COMFY_BASE / "web_custom_versions" / "desktop_app",
)
DEFAULT_COMFY_EXTRA_MODELS = _env_path(
    "LOCAL_COMFY_EXTRA_MODELS_CONFIG",
    Path(os.environ.get("APPDATA", str(HOME / "AppData" / "Roaming")))
    / "ComfyUI"
    / "extra_models_config.yaml",
)
DEFAULT_COMFY_DB_URL = os.environ.get(
    "LOCAL_COMFY_DB_URL",
    f"sqlite:///{(DEFAULT_COMFY_USER / 'comfyui.db').as_posix()}",
)
DEFAULT_LANE_BENCHMARKS = _env_path(
    "LOCAL_RENDER_LANE_BENCHMARKS",
    LOCAL_MEDIA_ROOT / "config" / "render_lane_benchmarks.local.json",
)
DEFAULT_FILENAME_PREFIX_ROOT = os.environ.get(
    "LOCAL_WAN_FILENAME_PREFIX_ROOT",
    "video/local_media_workbench",
).rstrip("/")


def default_filename_prefix(run_name: str) -> str:
    return f"{DEFAULT_FILENAME_PREFIX_ROOT}/{run_name}"
