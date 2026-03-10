---
name: repo-d-setup-diagnostics
description: Diagnose <PRIVATE_REPO_D> setup wizard and runtime state issues. Use when debugging LM Studio/Kokoro/Lovense setup paths, renderer hydration, profile persistence, overlay/background behavior, startup acceptance, or audio-baseline drift.
---

# Repo D Sandbox Setup Diagnostics

Use this skill for setup and runtime-state troubleshooting.

## Workflow

1. Reproduce the issue and capture exact user action sequence.
2. Inspect renderer diagnostics markers:
   - `hydrate.ok`
   - `repo_d.load_*`
   - `background.*`
   - `overlay.*`
3. Validate setup surfaces (LM Studio, Kokoro, Lovense, model selection) and persistence.
4. Validate startup acceptance when the issue spans launch behavior:
   - no empty console windows
   - no backend-only success for desktop lanes
   - no relaunch over stale windows
   - state restore remains intact
5. Use the current working-audio baseline when speech behavior changed.
6. Verify safety behaviors:
   - API key redaction in logs/export.
   - Profile export strips sensitive values.
5. Run integration smoke when behavior spans app boundaries:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/integration_smoke.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_full_app.ps1
```

## Output Requirements

- Root cause statement tied to concrete files.
- Minimal fix plan with affected modules.
- Validation commands and outcomes.
- Explicit undone status if startup acceptance or audio-baseline expectations still fail.
## Scope Boundary

Use this skill only for the `repo-d-setup-diagnostics` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- Diagnostic markers: `references/diagnostic-markers.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
