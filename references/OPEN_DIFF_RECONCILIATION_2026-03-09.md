# Open Diff Reconciliation - 2026-03-09

Current documentation reconciliation for the local open diffs in this repo.

## Current diff lanes

### Skill inventory refresh

Changed surface:
- `README.md`
- `references/skill-catalog.md`

Contract:
- the overlay skill counts and inventory descriptions must match the current restore baseline
- representative catalog entries must cover the newly added or upgraded skill lanes

### VS Code overlay restore handling

Changed surface:
- `references/vscode-skill-handling.md`

Contract:
- built-in skill handling and additive overlay restore behavior must remain explicitly documented
- restore counts and local control-file recovery steps must match the current overlay baseline

### Startup and removable-media skill expansion

Changed surface:
- `skill-candidates/desktop-startup-acceptance/SKILL.md`
- `skill-candidates/repo-a-host-admin-ops/SKILL.md`
- `skill-candidates/usb-export-reconcile/SKILL.md`

Contract:
- the skill set must explicitly cover workstation startup acceptance, admin-host startup ownership, and USB-as-GitHub reconcile discipline reflected in current cross-repo open diffs

### Existing skill upgrades

Changed surface:
- `skill-candidates/docs-alignment-lock/SKILL.md`
- `skill-candidates/repo-b-control-center-ops/SKILL.md`
- `skill-candidates/repo-b-mx3-router-contracts/SKILL.md`
- `skill-candidates/repo-b-preflight-doc-sync/SKILL.md`
- `skill-candidates/repo-d-setup-diagnostics/SKILL.md`
- `skill-candidates/repo-d-ui-guardrails/SKILL.md`
- `skill-candidates/skill-openclaw-nullclaw-integration/SKILL.md`

Contract:
- existing skills must reflect the current repo work on startup acceptance, ORT/provider exactness, OpenClaw provenance gating, reconciliation docs, and state-persistence expectations

## Evidence

- Cross-repo open-work radar: `references/cross_repo_open_work_radar_2026-03-09.clean.json`
- Extended radar including the no-commit Shockwave lane: `references/cross_repo_open_work_radar_2026-03-09.json`
- Arbiter pass for changed/new skills: `.tmp/arbiter-skill-pass-20260309.json`
- Skill audit for changed/new skills: `.tmp/skill-audit-20260309.json`
