---
name: repo-d-ui-guardrails
description: Enforce <PRIVATE_REPO_D> AGENTS.md guardrails for UI/Electron work. Use when modifying apps/desktop, packages/ui, packages/engine, packages/services, or docs tied to deterministic visuals, no-download policy, local-only behavior, and no-CI constraints.
---

# Repo D Sandbox UI Guardrails

Use this skill to keep <PRIVATE_REPO_D> changes compliant with repository rules.

## Workflow

1. Read `AGENTS.md` and `README.md` before editing.
2. Identify whether changes touch visuals, startup flow, assets, or docs.
3. Apply guardrails before coding:
   - Do not add `.github/workflows/*` or CI automation.
   - Keep deterministic visuals behind explicit toggles or presets.
   - Do not add runtime asset downloads.
   - Keep front-end boundaries intact; do not embed out-of-scope orchestration logic.
   - Do not change Electron boot/renderer readiness sequencing without explicit validation notes.
4. Update progress docs on scoped work:
   - `docs/SCOPE_TRACKER.md`
   - `docs/TODO.md`
5. Include a status block in notes/PR summary:
   - scope lane(s),
   - changed files,
   - validation commands with pass/fail,
   - remaining blockers.
6. Run local checks and report results.

## Required Checks

Run from repo root:

```bash
npm install
npm run build
npm run dist
npm run lint
npm run format
```

When startup flow or renderer wiring changes, also run:

```bash
npm run verify-startup
npm run dev
```
## Scope Boundary

Use this skill only for the `repo-d-ui-guardrails` lane and workflow defined in this file and its references.

Do not use this skill for unrelated lanes; route those through `$skill-hub` and the most specific matching skill.

## References

- Guardrail summary: `references/guardrails.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
