from __future__ import annotations

# Several imported names below are intentionally exposed as module attributes
# for split runtime helper modules that receive this module object at runtime.
# ruff: noqa: F401
import copy
import ipaddress
import json
import os
import subprocess
import sys
import time
import urllib.error
from collections import Counter
from shutil import which
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .llm_advisor import advisor_model, available_models, request_local_advice
from .paths import windows_no_window_subprocess_kwargs
from .process_policy_db import status as process_policy_status
from .stack_runtime_common import _first_dict, _first_int, _first_str, _pick_dict, _pick_str, _sanitize_path_hint
from .stack_runtime_processes import (
    _codex_rows as _codex_rows_impl,
    _codex_watch_enabled as _codex_watch_enabled_impl,
    _local_supervision_snapshot as _local_supervision_snapshot_impl,
    _powershell_json as _powershell_json_impl,
    _process_rows as _process_rows_impl,
    _psutil_process_rows as _psutil_process_rows_impl,
    _windows_no_window_subprocess_kwargs as _windows_no_window_subprocess_kwargs_impl,
)
from .stack_runtime_profiles import (
    ENABLE_CODEX_WATCH_ENV,
    KNOWN_STACK_MODES,
    POLL_PROFILE_ENV,
    POLL_PROFILE_OVERRIDES,
    STACK_HEALTH_URL_ENV,
    STACK_MODE_ENV,
    STACK_POLL_PROFILES,
    StackPollProfile,
    load_poll_profile as load_poll_profile_impl,
    stack_health_url as stack_health_url_impl,
    stack_mode as stack_mode_impl,
)
from .stack_runtime_snapshot import (
    _fetch_stack_payload as _fetch_stack_payload_impl,
    _normalize_last_seen as _normalize_last_seen_impl,
    _normalize_stack_snapshot as _normalize_stack_snapshot_impl,
    _parse_mx3_runtime as _parse_mx3_runtime_impl,
    _parse_subagent_payload as _parse_subagent_payload_impl,
    _stack_health_target as _stack_health_target_impl,
    normalize_mx3_from_events as normalize_mx3_from_events_impl,
    stack_health_target as stack_health_target_impl,
    stack_runtime_snapshot as stack_runtime_snapshot_impl,
    summarize_subagents_from_events as summarize_subagents_from_events_impl,
)

try:
    import psutil
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    psutil = None


STACK_TIMEOUT_SECONDS = 2.0
STACK_RUNTIME_CACHE_SECONDS = 3.0
LOCAL_SUPERVISION_CACHE_SECONDS = 5.0

_STACK_RUNTIME_CACHE = {
    "expires_at": 0.0,
    "payload": None,
}
_LOCAL_SUPERVISION_CACHE = {
    "expires_at": 0.0,
    "payload": None,
}

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_LOCAL_PROCESS_COMMAND = r"""
$targets = @('electron.exe','python.exe','LM Studio.exe','lms.exe')
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -in $targets -or
    ($_.CommandLine -match 'media-workbench' -or
     $_.CommandLine -match 'skill-arbiter' -or
     $_.CommandLine -match 'qwen[- ]training[- ]workbench' -or
     $_.CommandLine -match 'run_complete_media_loop.py' -or
     $_.CommandLine -match 'run_wan_flf2v.py')
  } |
  Select-Object Name,ProcessId,CommandLine |
  ConvertTo-Json -Depth 4
"""

_CODEX_PROCESS_COMMAND = r"""
$targets = @('Code.exe','codex.exe')
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -in $targets -or
    $_.CommandLine -match 'codex.exe' -or
    $_.CommandLine -match '\.code-workspace'
  } |
  Select-Object Name,ProcessId,CommandLine |
  ConvertTo-Json -Depth 4
"""


def _psutil_process_rows(include_codex: bool = False):
    return _psutil_process_rows_impl(sys.modules[__name__], include_codex=include_codex)


def _windows_no_window_subprocess_kwargs(kwargs=None):
    return _windows_no_window_subprocess_kwargs_impl(sys.modules[__name__], kwargs)


def _powershell_json(command: str):
    return _powershell_json_impl(sys.modules[__name__], command)


def _process_rows():
    return _process_rows_impl(sys.modules[__name__])


def _codex_watch_enabled() -> bool:
    return _codex_watch_enabled_impl(sys.modules[__name__])


def _codex_rows():
    return _codex_rows_impl(sys.modules[__name__])


def _local_supervision_snapshot(*, refresh: bool = False, include_advisor_note: bool = False):
    return _local_supervision_snapshot_impl(
        sys.modules[__name__],
        refresh=refresh,
        include_advisor_note=include_advisor_note,
    )


def stack_mode() -> str:
    return stack_mode_impl(sys.modules[__name__])


def stack_health_url() -> str:
    return stack_health_url_impl(sys.modules[__name__])


def _stack_health_target(url: str) -> str:
    return _stack_health_target_impl(sys.modules[__name__], url)


def stack_health_target() -> str:
    return stack_health_target_impl(sys.modules[__name__])


def load_poll_profile():
    return load_poll_profile_impl(sys.modules[__name__])


def _normalize_last_seen(events):
    return _normalize_last_seen_impl(sys.modules[__name__], events)


def summarize_subagents_from_events(events, *, max_items: int = 6):
    return summarize_subagents_from_events_impl(sys.modules[__name__], events, max_items=max_items)


def _parse_mx3_runtime(payload):
    return _parse_mx3_runtime_impl(sys.modules[__name__], payload)


def _parse_subagent_payload(payload):
    return _parse_subagent_payload_impl(sys.modules[__name__], payload)


def _normalize_stack_snapshot(payload, *, requested_mode: str, source: str):
    return _normalize_stack_snapshot_impl(sys.modules[__name__], payload, requested_mode=requested_mode, source=source)


def _fetch_stack_payload(url: str):
    return _fetch_stack_payload_impl(sys.modules[__name__], url)


def stack_runtime_snapshot(*, fallback_events=None, force_refresh: bool = False, refresh_local_supervision: bool = False):
    return stack_runtime_snapshot_impl(
        sys.modules[__name__],
        fallback_events=fallback_events,
        force_refresh=force_refresh,
        refresh_local_supervision=refresh_local_supervision,
    )


def normalize_mx3_from_events(events):
    return normalize_mx3_from_events_impl(sys.modules[__name__], events)
