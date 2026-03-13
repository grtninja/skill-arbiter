# VS Code / Codex Baseline Handling

This repository treats VS Code/Codex built-ins as upstream baseline and overlays repository-owned skills on top.

## Policy

- Built-ins remain enabled.
- `.system` skills remain enabled.
- Overlay candidates are additive.
- This repo does not disable or replace upstream skills to make overlays work.

## Current reconciliation model

The live inventory pipeline checks:

- installed top-level skills in `$CODEX_HOME/skills`
- installed `.system` skills
- overlay candidates in `skill-candidates/`
- official upstream baseline from `openai/skills`
- local Codex configuration in `%USERPROFILE%\\.codex`
- Codex app instruction surfaces via `AGENTS.md`
- VS Code instruction surfaces under `.vscode/`
- GitHub Copilot instruction and prompt surfaces under `.github/`
- curated source references already tracked by the repo

It also tags each skill row with:

- `ownership`
- `legitimacy_status`
- `legitimacy_reason`

so official built-ins, repo-owned skills, and unowned local installs do not collapse into the same trust lane.

The machine-generated catalog is the current inventory reference:

- `references/skill-catalog.md`
- `references/skill-vetting-report.md`

## Recovery flow

When overlays are missing after a host/editor refresh:

1. Open the NullClaw desktop app.
2. Let the app complete:
   - app open
   - agent attach/start
   - self-checks
   - inventory refresh
3. Review missing-overlay and missing-builtin drift in the inventory tables.
4. Restore overlay candidates additively from `skill-candidates/`.
5. Re-run admission and source-risk review before broad use.

## Current expected counts

These are refreshed by the generated catalog rather than maintained by hand:

- top-level built-ins
- `.system` built-ins
- overlay candidates
- total expected additive inventory

## Guardrails

1. Do not restore unknown third-party content blindly.
2. Do not treat public catalog presence as trusted provenance.
3. Do not use overlay recovery to bypass quarantine or source-risk policy.
4. Keep `references/skill-catalog.md` current after any inventory-affecting change.
