#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from ctypes import WinDLL, c_void_p, wintypes
from pathlib import Path
from urllib import error, request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skill_arbiter.paths import DEFAULT_AGENT_HOST, DEFAULT_AGENT_PORT, windows_no_window_subprocess_kwargs

APP_TITLE = "Skill Arbiter Security Console"
APP_ID = "grtninja.SkillArbiterSecurityConsole"
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE = 0x0040
_ICON_HANDLE = c_void_p()


def _console_free_python() -> str:
    executable = Path(sys.executable).resolve()
    if sys.platform != "win32":
        return str(executable)
    if executable.name.lower() == "pythonw.exe":
        return str(executable)
    sibling = executable.with_name("pythonw.exe")
    if sibling.is_file():
        return str(sibling)
    return str(executable)


def _desktop_root() -> Path:
    return Path(__file__).resolve().parents[1] / "apps" / "nullclaw-desktop"


def _electron_binary() -> Path:
    return _desktop_root() / "node_modules" / "electron" / "dist" / "SkillArbiterSecurityConsole.exe"


def _spawn_electron_hidden() -> int:
    electron_binary = _electron_binary()
    if not electron_binary.is_file():
        return 2

    env = dict(os.environ)
    env.pop("ELECTRON_RUN_AS_NODE", None)

    kwargs: dict[str, object] = {
        "cwd": str(_desktop_root()),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    subprocess.Popen([str(electron_binary), "."], **windows_no_window_subprocess_kwargs(kwargs))
    return 0


def _health() -> dict[str, object] | None:
    try:
        with request.urlopen(f"http://{DEFAULT_AGENT_HOST}:{DEFAULT_AGENT_PORT}/v1/health", timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))
    except (error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def _icon_path() -> Path:
    return Path(__file__).resolve().parents[1] / "apps" / "nullclaw-desktop" / "assets" / "skill_arbiter_ntm_v4.ico"


def _apply_process_branding() -> None:
    if sys.platform != "win32":
        return
    try:
        WinDLL("shell32").SetCurrentProcessExplicitAppUserModelID(wintypes.LPCWSTR(APP_ID))
    except OSError:
        return


def _apply_window_icon() -> None:
    if sys.platform != "win32":
        return
    icon_path = _icon_path()
    if not icon_path.is_file():
        return
    try:
        user32 = WinDLL("user32")
        global _ICON_HANDLE
        _ICON_HANDLE = user32.LoadImageW(None, str(icon_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not _ICON_HANDLE:
            return
        deadline = time.time() + 8.0
        hwnd = 0
        while not hwnd and time.time() < deadline:
            hwnd = user32.FindWindowW(None, APP_TITLE)
            if not hwnd:
                time.sleep(0.2)
        if hwnd:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, _ICON_HANDLE)
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, _ICON_HANDLE)
    except OSError:
        return


def _attach_or_start_agent(*_args: object) -> None:
    _apply_window_icon()
    if _health():
        return
    script = Path(__file__).resolve().parent / "nullclaw_agent.py"
    subprocess.Popen(
        [_console_free_python(), str(script), "--host", DEFAULT_AGENT_HOST, "--port", str(DEFAULT_AGENT_PORT)],
        **windows_no_window_subprocess_kwargs(
            {
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "close_fds": True,
            }
        ),
    )
    for _ in range(12):
        if _health():
            _apply_window_icon()
            return
        time.sleep(0.5)


def main() -> int:
    if "--spawn-electron-hidden" in sys.argv[1:]:
        return _spawn_electron_hidden()

    try:
        import webview
    except ModuleNotFoundError:
        print(
            "pywebview is required for the embedded Skill Arbiter desktop UI. "
            "Install it with `python -m pip install pywebview`.",
            file=sys.stderr,
        )
        return 2

    ui_path = _desktop_root() / "ui" / "index.html"
    if not ui_path.is_file():
        print(f"missing UI file: {ui_path}", file=sys.stderr)
        return 2

    _apply_process_branding()
    window = webview.create_window(
        APP_TITLE,
        ui_path.as_uri(),
        width=1380,
        height=920,
        min_size=(1120, 760),
        text_select=True,
        background_color="#08101A",
    )
    webview.start(_attach_or_start_agent, window, gui="edgechromium")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
