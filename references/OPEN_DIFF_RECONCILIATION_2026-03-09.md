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

### Collaboration learning and heterogeneous validation

Changed surface:
- `README.md`
- `skill_arbiter/collaboration.py`
- `skill_arbiter/agent_server.py`
- `skill-candidates/heterogeneous-stack-validation/*`

Contract:
- the desktop app records collaboration outcomes from real governed work
- collaboration outcomes feed trust-ledger and skill-game scoring
- heterogeneous multi-host validation is represented as a governed skill candidate instead of an ad hoc one-off note

### Full sweep regeneration

Changed surface:
- `references/skill-catalog.md`
- `references/skill-vetting-report.md`

Contract:
- the machine-generated skill inventory and vetting report must reflect the current live sweep state
- the published truth for this pass is:
  - `official_trusted = 37`
  - `owned_trusted = 61`
  - `accepted_review = 0`
  - `needs_review = 0`
  - `blocked_hostile = 0`
  - `incident_count = 0`

### Full candidate sweep and consolidation evidence

Changed surface:
- `skill-candidates/*`
- `references/OPEN_DIFF_RECONCILIATION_2026-03-09.md`

Contract:
- every candidate skill must be audited in one governed pass
- generated artifacts under candidate roots must be removed before completion
- overlap and upgrade pressure must be recorded as consolidation evidence instead of guessed ad hoc
- the published truth for the 2026-03-12 sweep is:
  - `skills_scanned = 124`
  - `high_count = 0`
  - `medium_count = 0`
  - `low_count = 1`
  - the only remaining finding is `gh-issues` with `skill_md_large`
  - candidate artifact hygiene removed `12` generated `__pycache__` directories
  - installed-skill overlap audit reported `10` pairs at or above the boundary-blur threshold with `imagegen <-> speech` as the strongest current overlap signal

### Skill game longitudinal mapping

Changed surface:
- `skill_arbiter/skill_game_runtime.py`
- `apps/nullclaw-desktop/ui/index.html`
- `apps/nullclaw-desktop/ui/app.js`
- `README.md`

Contract:
- original skill levels mapped from `references/skill-progression.md` are part of the current skill game
- this is longitudinal tracking for the real skill estate, not a deprecated compatibility lane
- the desktop console and API must report:
  - `original_skill_levels`
  - `original_skill_count`
  - governed collaboration outcomes tied to those skills over time

## Evidence

- Cross-repo open-work radar: `references/cross_repo_open_work_radar_2026-03-09.clean.json`
- Extended radar including the no-commit Shockwave lane: `references/cross_repo_open_work_radar_2026-03-09.json`
- Arbiter pass for changed/new skills: `.tmp/arbiter-skill-pass-20260309.json`
- Skill audit for changed/new skills: `.tmp/skill-audit-20260309.json`
- Full candidate artifact scan: `.tmp/artifact-scan-skill-candidates-20260312.json`
- Full candidate artifact cleanup: `.tmp/artifact-clean-skill-candidates-20260312.json`
- Full candidate audit: `.tmp/skill-audit-all-candidates-20260312.json`
- Installed-skill overlap audit: `.tmp/skill-overlap-20260312.json`
- Heterogeneous validation arbiter evidence: `.tmp/arbiter-heterogeneous-stack-validation-20260312.json`
- Heterogeneous validation audit evidence: `.tmp/skill-audit-heterogeneous-stack-validation-20260312.json`
- Skill-installer-plus feedback: `.tmp/skill-installer-plus-feedback-heterogeneous-stack-validation-20260312.json`
- Collaboration log and skill-game ledger are local-only state under the NullClaw app data root and are intentionally not tracked
