---
name: vrm-sandbox-setup-diagnostics
description: Diagnose VRM-Sandbox setup wizard and runtime state issues. Use when debugging LM Studio/Kokoro/Lovense setup paths, renderer hydration, profile persistence, or overlay/background behavior.
---

# VRM Sandbox Setup Diagnostics

Use this skill for setup and runtime-state troubleshooting.

## Workflow

1. Reproduce the issue and capture exact user action sequence.
2. Inspect renderer diagnostics markers:
   - `hydrate.ok`
   - `vrm.load_*`
   - `background.*`
   - `overlay.*`
3. Validate setup surfaces (LM Studio, Kokoro, Lovense, model selection) and persistence.
4. Verify safety behaviors:
   - API key redaction in logs/export.
   - Profile export strips sensitive values.
5. Run integration smoke when behavior spans app boundaries:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/integration_smoke.ps1
```

## Output Requirements

- Root cause statement tied to concrete files.
- Minimal fix plan with affected modules.
- Validation commands and outcomes.

## References

- Diagnostic markers: `references/diagnostic-markers.md`
