---
name: "repo-b-hardware-first"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Enforce hardware-first diagnosis and fixes in <PRIVATE_REPO_B>. Use for runtime probe, telemetry, inference, and integration failures where strict real-hardware behavior, no new stubs, deterministic diagnostics, and no unrequested driver/runtime mutation are required."
---

# REPO_B Shim Hardware First

Use this skill to troubleshoot and fix shim issues with real-hardware assumptions.

## Operating Rules

1. Assume hardware exists and is the required path.
2. Do not add new stubs, fake fallbacks, or simulation shortcuts.
3. Do not modify or refresh driver/runtime/firmware unless explicitly requested.
4. Keep strict env modes explicit during diagnosis.
5. Treat the Windows MX3 lane contract as fixed unless evidence disproves it:
   - `127.0.0.1:10000` = MX3 manager / device-management boundary
   - `127.0.0.1:9000` = aggregate inference/router plane
   - `127.0.0.1:2337` = hosted chat lane
   - `127.0.0.1:2236` = standalone embedding lane
6. Treat `:9000` as an aggregate inference plane, not as the driver itself.
7. Use unlock-before-feeder doctrine:
   - unlock / `prepare-stop`
   - load/apply DFP runtime
   - enable feeder
8. On Windows, treat “reboot required” without a real device-problem code as a false-flag tell until proven otherwise.
9. Preserve the known-good service boundary for the hardware lane:
   - `<PRIVATE_REPO_B>\.venv\Scripts\python.exe`
   - backed by `<PRIVATE_WINDOWS_PYTHON>\python.exe`
10. Use the official examples repo before inventing MX3 lifecycle behavior:
   - `<PRIVATE_MX3_EXAMPLES_REPO>`

## Strict-Diagnosis Workflow

1. Set strict environment flags.
2. Confirm the manager/device boundary at `:10000` before trusting any HTTP service on `:9000`.
3. Run doctor and probe checks.
4. Run strict preflight profiles.
5. Verify host/runtime versions against `config/mx3_runtime_baseline.json` before any host mutation.
6. Fix root cause in real execution path first (routing, preload, lifecycle, endpoint readiness).
7. If feeder/runtime state is wrong, force the recovery order to stay explicit:
   - `prepare-stop -> load-model/apply-dfp -> feeder-config`
8. Re-run checks and capture evidence.

## Scope Boundary

Use this skill only for real-hardware diagnosis and fix verification.

Do not use this skill for:

1. PR governance/doc lockstep only workflows.
2. Control Center process/restart UX operations.
3. Agent Bridge safety-mode configuration.

## Commands

```bash
$env:REPO_B_ONLY = "1"
$env:REPO_B_FORCE_REAL = "1"
$env:REPO_B_INFERENCE_PROVIDER = "repo_b_only"
python -m memryx_mx3_python_shim --doctor
python shim_hw_test.py --json --require-hardware
```

```powershell
pwsh -File tools/preflight.ps1 -Fast
pwsh -File tools/preflight.ps1 -Hardware -ForceReal -MemryxOnly -VerboseOutput
```

## References

- Strict command matrix: `references/strict-commands.md`
- Windows non-reboot recovery doctrine: `<PRIVATE_REPO_B>\docs\MEMRYX_WINDOWS_MX3_NON_REBOOT_RECOVERY_NOTE.md`
- Operator reset runbook: `<PRIVATE_REPO_B>\docs\MX3_RUNTIME_RESET_RUNBOOK.md`

## Validated Windows MX3 recovery sequence

This sequence is the recorded good working state for Windows MX3 recovery without a host reboot:

1. `POST http://127.0.0.1:9000/api/runtime/prepare-stop`
2. `<PRIVATE_REPO_B>\.venv\Scripts\python.exe <PRIVATE_REPO_B>\tools\switch_mx3_dfp_runtime.py --mode apply --profile-name llm_generalist_runtime`
3. Re-read `/api/model-service/state`
4. Re-read `/telemetry/report`
5. Enable feeder only after runtime load is present
6. Accept only when:
   - `enabled = true`
   - `active = true`
   - `status = live`
   - `feeder_runtime_alignment = aligned`
   - `last_provider = mx3`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
