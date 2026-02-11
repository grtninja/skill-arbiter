---
name: repo-b-preflight-doc-sync
description: Enforce <PRIVATE_REPO_B> preflight gates and documentation lockstep. Use before PRs to run required validation profiles and keep README.md, docs/PROJECT_SCOPE.md, and docs/SCOPE_TRACKER.md synchronized with shipped behavior.
---

# REPO_B Shim Preflight and Doc Sync

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
pwsh -File tools/preflight.ps1 -Hardware -ForceReal -repo_bOnly -VerboseOutput
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

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
