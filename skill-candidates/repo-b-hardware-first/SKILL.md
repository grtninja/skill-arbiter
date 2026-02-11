---
name: repo-b-hardware-first
description: Enforce hardware-first diagnosis and fixes in <PRIVATE_REPO_B>. Use for runtime probe, telemetry, inference, and integration failures where strict real-hardware behavior, no new stubs, and deterministic diagnostics are required.
---

# REPO_B Shim Hardware First

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

## Scope Boundary

Use this skill only for real-hardware diagnosis and fix verification.

Do not use this skill for:

1. PR governance/doc lockstep only workflows (use `repo-b-preflight-doc-sync`).
2. Control Center process/restart UX operations (use `repo-b-control-center-ops`).
3. Agent Bridge safety-mode configuration (use `repo-b-agent-bridge-safety`).

## Commands

```bash
repo_b_ONLY=1 repo_b_FORCE_REAL=1 REPO_B_INFERENCE_PROVIDER=repo_b_only python3 -m repo_b_repo_b_python_shim --doctor
repo_b_ONLY=1 repo_b_FORCE_REAL=1 REPO_B_INFERENCE_PROVIDER=repo_b_only python3 shim_hw_test.py --json --require-hardware
```

```powershell
pwsh -File tools/preflight.ps1 -Fast
pwsh -File tools/preflight.ps1 -Hardware -ForceReal -repo_bOnly -VerboseOutput
```

## References

- Strict command matrix: `references/strict-commands.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
