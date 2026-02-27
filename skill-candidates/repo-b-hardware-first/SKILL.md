---
name: repo-b-hardware-first
description: Enforce hardware-first diagnosis and fixes in <PRIVATE_REPO_B>. Use for runtime probe, telemetry, inference, and integration failures where strict real-hardware behavior, no new stubs, deterministic diagnostics, and no unrequested driver/runtime mutation are required.
---

# REPO_B Shim Hardware First

Use this skill to troubleshoot and fix shim issues with real-hardware assumptions.

## Operating Rules

1. Assume hardware exists and is the required path.
2. Do not add new stubs, fake fallbacks, or simulation shortcuts.
3. Do not modify or refresh driver/runtime/firmware unless explicitly requested.
4. Keep strict env modes explicit during diagnosis.

## Strict-Diagnosis Workflow

1. Set strict environment flags.
2. Run doctor and probe checks.
3. Run strict preflight profiles.
4. Verify host/runtime versions against `config/mx3_runtime_baseline.json` before any host mutation.
5. Fix root cause in real execution path first (routing, preload, lifecycle, endpoint readiness).
6. Re-run checks and capture evidence.

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

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
