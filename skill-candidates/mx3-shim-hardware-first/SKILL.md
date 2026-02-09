---
name: mx3-shim-hardware-first
description: Enforce hardware-first diagnosis and fixes in <MX3_SHIM_REPO>. Use for runtime probe, telemetry, inference, and integration failures where strict real-hardware behavior, no new stubs, and deterministic diagnostics are required.
---

# MX3 Shim Hardware First

Use this skill to troubleshoot and fix shim issues with real-hardware assumptions.

## Operating Rules

1. Assume hardware exists and is the required path.
2. Do not add new stubs, fake fallbacks, or simulation shortcuts.
3. Keep strict env modes explicit during diagnosis.

## Strict-Diagnosis Workflow

1. Set strict environment flags.
2. Run doctor and probe checks.
3. Run strict preflight profiles.
4. Fix root cause in real execution path.
5. Re-run checks and capture evidence.

## Commands

```bash
MEMRYX_ONLY=1 MEMRYX_FORCE_REAL=1 MX3_INFERENCE_PROVIDER=mx3_only python3 -m memryx_mx3_python_shim --doctor
MEMRYX_ONLY=1 MEMRYX_FORCE_REAL=1 MX3_INFERENCE_PROVIDER=mx3_only python3 shim_hw_test.py --json --require-hardware
```

```powershell
pwsh -File tools/preflight.ps1 -Fast
pwsh -File tools/preflight.ps1 -Hardware -ForceReal -MemryxOnly -VerboseOutput
```

## References

- Strict command matrix: `references/strict-commands.md`
