from __future__ import annotations

import copy
from types import ModuleType
from typing import Any


def _psutil_process_rows(module: ModuleType, include_codex: bool = False) -> list[dict[str, Any]]:
    if module.psutil is None:
        return []
    rows: list[dict[str, Any]] = []
    target_names = {"electron.exe", "python.exe", "lm studio.exe", "lms.exe"}
    if include_codex:
        target_names |= {"code.exe", "codex.exe"}
    for proc in module.psutil.process_iter(["name", "pid", "cmdline"]):
        try:
            info = proc.info
        except (module.psutil.NoSuchProcess, module.psutil.AccessDenied, module.psutil.ZombieProcess):
            continue
        name = module._first_str(info.get("name"), "")
        command_parts = info.get("cmdline") or []
        if isinstance(command_parts, str):
            command = command_parts
        else:
            command = " ".join(part for part in command_parts if isinstance(part, str))
        lowered_name = name.lower()
        lowered_command = command.lower()
        local_match = lowered_name in target_names or any(
            token in lowered_command
            for token in (
                "media-workbench",
                "skill-arbiter",
                "qwen-training-workbench",
                "qwen training workbench",
                "run_complete_media_loop.py",
                "run_wan_flf2v.py",
            )
        )
        codex_match = include_codex and (
            lowered_name in {"code.exe", "codex.exe"} or "codex.exe" in lowered_command or ".code-workspace" in lowered_command
        )
        if not local_match and not codex_match:
            continue
        rows.append(
            {
                "Name": name,
                "ProcessId": int(info.get("pid") or 0),
                "CommandLine": command,
            }
        )
    return rows


def _windows_no_window_subprocess_kwargs(module: ModuleType, kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
    return module.windows_no_window_subprocess_kwargs(kwargs)


def _powershell_json(module: ModuleType, command: str) -> Any:
    if module.os.name != "nt":
        return []
    executable = module.which("powershell.exe") or module.which("pwsh")
    if not executable:
        return []
    completed = module.subprocess.run(
        [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
        **module._windows_no_window_subprocess_kwargs(),
    )
    if completed.returncode != 0:
        return []
    raw = completed.stdout.strip()
    if not raw:
        return []
    try:
        return module.json.loads(raw)
    except module.json.JSONDecodeError:
        return []


def _process_rows(module: ModuleType) -> list[dict[str, Any]]:
    psutil_rows = module._psutil_process_rows()
    if psutil_rows:
        return psutil_rows
    payload = module._powershell_json(module._LOCAL_PROCESS_COMMAND)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _codex_watch_enabled(module: ModuleType) -> bool:
    return module._first_str(module.os.environ.get(module.ENABLE_CODEX_WATCH_ENV), "0").lower() in {"1", "true", "yes", "on"}


def _codex_rows(module: ModuleType) -> list[dict[str, Any]]:
    if not module._codex_watch_enabled():
        return []
    psutil_rows = module._psutil_process_rows(include_codex=True)
    if psutil_rows:
        return [
            row
            for row in psutil_rows
            if module._first_str(row.get("Name"), "").lower() in {"code.exe", "codex.exe"}
            or "codex.exe" in module._first_str(row.get("CommandLine"), "").lower()
            or ".code-workspace" in module._first_str(row.get("CommandLine"), "").lower()
        ]
    payload = module._powershell_json(module._CODEX_PROCESS_COMMAND)
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _local_supervision_snapshot(
    module: ModuleType,
    *,
    refresh: bool = False,
    include_advisor_note: bool = False,
) -> dict[str, Any]:
    now = module.time.time()
    if not refresh and module._LOCAL_SUPERVISION_CACHE["expires_at"] > now and module._LOCAL_SUPERVISION_CACHE["payload"] is not None:
        return copy.deepcopy(module._LOCAL_SUPERVISION_CACHE["payload"])
    rows = module._process_rows()
    codex_rows = module._codex_rows()
    vscode_windows = 0
    codex_processes = 0
    active_tasks: list[str] = []
    workspace_hints: list[str] = []
    for row in rows:
        name = module._first_str(row.get("Name"), "")
        command = module._first_str(row.get("CommandLine"), "")
        lowered = command.lower()
        if "run_complete_media_loop.py" in lowered:
            active_tasks.append("media-workbench: complete_media_loop")
        elif "run_wan_flf2v.py" in lowered:
            active_tasks.append("media-workbench: raw render slice")
        elif "starframe-media-workbench" in lowered and "electron.exe" in lowered:
            active_tasks.append("media-workbench: desktop live")
        elif "qwen training workbench" in lowered:
            active_tasks.append("qwen-training: desktop live")
        elif "skill-arbiter" in lowered and ("electron.exe" in lowered or "python.exe" in lowered):
            active_tasks.append("skill-arbiter: local supervisor live")
        if name == "Code.exe" and "--type=" not in command:
            vscode_windows += 1
    for row in codex_rows:
        lowered = module._first_str(row.get("CommandLine"), "").lower()
        if "codex.exe" in lowered:
            codex_processes += 1
        if ".code-workspace" in lowered:
            workspace_hints.append(module._sanitize_path_hint(module._first_str(row.get("CommandLine"), "")))
    model_list = module.available_models(refresh=refresh)
    qwen_models = [model for model in model_list if "qwen" in model.lower() or "huihui" in model.lower()]
    selected_model = module.advisor_model(refresh=refresh)
    process_policy = module.process_policy_status()
    findings = [
        f"vscode_windows={vscode_windows if module._codex_watch_enabled() else 'disabled'}",
        f"codex_processes={codex_processes if module._codex_watch_enabled() else 'disabled'}",
        f"active_tasks={len(active_tasks)}",
        f"qwen_models={len(qwen_models)}",
        f"advisor_model={selected_model}",
        f"process_policy={process_policy.get('integrity', 'unknown')}",
    ]
    supervisor_note = ""
    if include_advisor_note:
        supervisor_note = module.request_local_advice("agent_runtime_supervision", findings, timeout_s=0.8)
    if not supervisor_note:
        if qwen_models:
            supervisor_note = (
                f"Watching {len(active_tasks)} active task(s) through local Qwen lane "
                f"{selected_model}; richer advisor reply unavailable, continue supervised polling."
            )
        else:
            supervisor_note = "Local supervisor is watching VS Code and host activity, but no live Qwen lane responded yet."
    payload = {
        "available": True,
        "observed_process_count": len(rows),
        "vscode": {
            "window_count": vscode_windows,
            "workspace_hints": workspace_hints[:4],
            "watch_enabled": module._codex_watch_enabled(),
        },
        "codex": {
            "process_count": codex_processes,
            "watch_enabled": module._codex_watch_enabled(),
        },
        "active_tasks": list(dict.fromkeys(active_tasks))[:8],
        "advisor": {
            "selected_model": selected_model,
            "available_models": model_list[:24],
            "qwen_models": qwen_models[:16],
            "note": supervisor_note,
        },
        "process_policy": {
            "database": process_policy.get("database"),
            "integrity": process_policy.get("integrity"),
            "policies": process_policy.get("policies", []),
            "denied_process_counts": process_policy.get("denied_process_counts", {}),
        },
    }
    module._LOCAL_SUPERVISION_CACHE["payload"] = copy.deepcopy(payload)
    module._LOCAL_SUPERVISION_CACHE["expires_at"] = now + module.LOCAL_SUPERVISION_CACHE_SECONDS
    return payload
