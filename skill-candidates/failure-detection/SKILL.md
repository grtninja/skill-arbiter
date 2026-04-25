---
name: failure-detection
description: Detect and classify startup, transport, process-ownership, and runtime-state failures in <PUBLIC_OPERATOR_SCOPE> before they are mistaken for success. Use when a cmd/PowerShell window flashes and disappears, a desktop app launches without a durable visible window, Electron or helper processes survive without a main window, feeder/runtime state gets stuck in target_not_loaded or similar false-ready states, MCP/local-agent transport reports Transport closed, or stale launcher/helper processes may be masking the real failure.
---

# Failure Detection

Use this skill to turn machine tells into hard failure gates instead of soft guesses.

## Hard Failure Tells

Treat each of these as a real failure until disproven:

1. `cmd.exe`, `powershell.exe`, or `pwsh.exe` flashes and disappears without a durable app surface.
2. The launcher returns, but no visible desktop window remains.
3. Electron, Python, or helper processes remain alive with no main-window ownership.
4. Repo-owned helper processes keep stacking after relaunch attempts.
5. The broker is healthy, but MCP or local-agent calls still report `Transport closed`.
6. MemryX feeder state stays in `target_not_loaded`, `disabled`, or similar limbo after a DFP switch.
7. LM Studio, bridge, or telemetry surfaces appear alive while the real runtime path is still unloaded.
8. Windows MX3 device reports "reboot required" but has no actual device problem:
   - `DEVPKEY_Device_IsRebootRequired = true`
   - `DEVPKEY_Device_ProblemCode = 0`
   - `DEVPKEY_Device_HasProblem = false`
   This is a stale PnP false flag on this workstation class and must be treated as a recovery/lock tell, not as the only permissible action.
9. The public shim plane on `:9000` looks healthy, but the dedicated MX3 management boundary is absent:
   - `mxa_manager.exe` / `MxaManagerSvc` missing
   - `127.0.0.1:10000` not owned by the vendor manager layer
   - feeder remains `target_not_loaded` or `unaligned`
   Treat this as a broken hardware-management contract, not as a successful startup.

On this machine specifically: a flashing console window is not cosmetic. It is a startup-failure tell.

## Workflow

1. Capture the visible tell first.
2. Confirm whether a durable app surface actually exists:
   - visible desktop window
   - valid main-window handle
   - repo-owned process tree
3. Separate ownership from illusion:
   - listener exists but wrong parent/process owner
   - helper survived but shell never came up
   - backend answered but frontend never materialized
4. Run stale-process mapping before retrying:
   - `keep`
   - `kill`
   - `suspect-but-verify`
   - `exclude`
5. If the lane is MemryX-related, consult the official examples repo before inventing lifecycle behavior:
   - official examples repo:
     `<PRIVATE_REPO_ROOT>\MemryX_eXamples`
   - authoritative Windows lifecycle example:
     `<PRIVATE_REPO_ROOT>\MemryX_eXamples\video_inference\pointcloud_from_depth\src\python_windows\lib\accl.py`
6. Treat DFP/runtime ownership as first-class:
   - use `prepare-stop -> mx3/load-model -> feeder-config`
   - do not treat feeder config alone as proof that the runtime is loaded
   - keep the lane split explicit:
     - `127.0.0.1:10000` = MX3 manager / hardware-management boundary
     - `127.0.0.1:9000` = aggregate inference plane
     - `127.0.0.1:2337` = hosted main chat/vision lane
     - `127.0.0.1:2236` = standalone embedding lane
7. Use unlock-before-feeder doctrine:
   - unlock / `prepare-stop`
   - load/apply DFP runtime
   - enable feeder
8. If `Transport closed` appears, distinguish the failing layer:
   - unified broker/service healthy
   - MCP stdio bridge broken
   - client session attachment broken
9. Only after the failure is classified should restart or cleanup happen.

## Canonical Evidence

Collect these before claiming a repair:

- exact launcher command used
- whether a visible app window exists
- main-window handle or equivalent proof
- repo-owned process list for the lane
- stale-process classification results
- listener/health evidence for the intended service
- for MemryX lanes: feeder state, selected DFP, runtime-load evidence, and whether the hardware was unlocked before feeder start
- for MCP/local-agent lanes: broker health plus transport failure distinction

## MemryX-Specific Rules

- Feeder lock or `target_not_loaded` is not a minor warning; it means the runtime lifecycle is incomplete.
- `:9000` is never the driver itself. It is the aggregate inference/router plane and must consume MX3 hardware through the dedicated manager/device boundary.
- `:10000` is the first-class hardware-management lane on this workstation. If it is absent or mismapped, treat MX3 as unavailable even when `:9000` still answers HTTP.
- Treat `:10000` as the device-management/driver-facing boundary that makes non-reboot Windows recovery possible.
- Public and private control surfaces must expose the real DFP/runtime load path, not just feeder overrides.
- Treat embeddings as feeder-independent truth when the embed lane is independently alive.
- Use official examples to confirm runtime close/unlock/open/download behavior before changing the repo contract.
- Never treat `udriver.dll` as an inference fallback on Windows; if only that DLL is discoverable, fail closed with a binding/runtime mismatch report.
- Host Python stays modern (3.12/3.13). Vendor service boundaries may remain 3.11-only; do not "fix" this by downgrading the whole stack.
- On this machine, the known-good MX3 service boundary is:
  `G:\GitHub\<PRIVATE_REPO_B>\.venv\Scripts\python.exe`
  backed by `%USERPROFILE%\AppData\Local\Programs\Python\Python311-mx3shim\python.exe`.
  If a watcher relaunches `:9000` on another interpreter and hardware disappears, classify that as launcher drift and repair it before touching LM Studio.

## Written-in-Stone Notes

These are first-class reference docs, not optional hints:

- Vendor-facing Windows recovery note:
  `G:\GitHub\<PRIVATE_REPO_B>\docs\MEMRYX_WINDOWS_MX3_NON_REBOOT_RECOVERY_NOTE.md`
- Operator reset runbook:
  `G:\GitHub\<PRIVATE_REPO_B>\docs\MX3_RUNTIME_RESET_RUNBOOK.md`

## Validated Windows MX3 recovery sequence

This sequence is the recorded good working state for Windows MX3 recovery without a full host reboot.
Reference artifact:
- `%USERPROFILE%\.codex\workstreams\mx3_in_place_reset_test_2026-04-10.json`

Exact sequence:
1. `POST http://127.0.0.1:9000/api/runtime/prepare-stop`
2. `G:\GitHub\<PRIVATE_REPO_B>\.venv\Scripts\python.exe G:\GitHub\<PRIVATE_REPO_B>\tools\switch_mx3_dfp_runtime.py --mode apply --profile-name llm_generalist_runtime --out %USERPROFILE%\.codex\workstreams\mx3_in_place_reset_test_2026-04-10.json`
3. Re-read `/api/model-service/state`
4. Re-read `/telemetry/report`
5. Enable feeder only after runtime load is present
6. Accept recovery only when all of the following are true:
   - `enabled = true`
   - `active = true`
   - `status = live`
   - `feeder_runtime_alignment = aligned`
   - `last_provider = mx3`

This is first-class doctrine and must be preferred over stale "full reboot only" assumptions.
