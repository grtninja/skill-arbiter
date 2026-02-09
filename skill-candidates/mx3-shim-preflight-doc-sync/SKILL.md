---
name: mx3-shim-preflight-doc-sync
description: Enforce <MX3_SHIM_REPO> preflight gates and documentation lockstep. Use before PRs to run required validation profiles and keep README.md, docs/PROJECT_SCOPE.md, and docs/SCOPE_TRACKER.md synchronized with shipped behavior.
---

# MX3 Shim Preflight and Doc Sync

Use this skill for PR-readiness and governance updates.

## Workflow

1. Run required preflight commands for the change scope.
2. Capture command evidence and failures with explicit repro notes.
3. Keep docs in lockstep for behavior changes.
4. Add target-PC rerun steps when hardware-only checks cannot run locally.

## Required Preflight Profiles

```powershell
pwsh -File tools/preflight.ps1 -Fast
pwsh -File tools/preflight.ps1 -Node
pwsh -File tools/preflight.ps1 -Hardware -ForceReal -MemryxOnly -VerboseOutput
```

```bash
python tools/preflight.py
```

## Documentation Lockstep

Review and update together when behavior changes:

- `README.md`
- `docs/PROJECT_SCOPE.md`
- `docs/SCOPE_TRACKER.md`

## References

- PR gate checklist: `references/pr-gate-checklist.md`
