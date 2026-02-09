---
name: vrm-sandbox-ui-guardrails
description: Enforce <VRM_SANDBOX_REPO> AGENTS.md guardrails for UI/Electron work. Use when modifying apps/desktop, packages/ui, packages/engine, packages/services, or docs tied to deterministic visuals, no-download policy, local-only behavior, and no-CI constraints.
---

# VRM Sandbox UI Guardrails

Use this skill to keep <VRM_SANDBOX_REPO> changes compliant with repository rules.

## Workflow

1. Read `AGENTS.md` and `README.md` before editing.
2. Identify whether changes touch visuals, startup flow, assets, or docs.
3. Apply guardrails before coding:
   - Do not add `.github/workflows/*` or CI automation.
   - Keep deterministic visuals behind explicit toggles or presets.
   - Do not add runtime asset downloads.
   - Keep front-end boundaries intact; do not embed out-of-scope orchestration logic.
4. Update progress docs on scoped work:
   - `docs/SCOPE_TRACKER.md`
   - `docs/TODO.md`
5. Run local checks and report results.

## Required Checks

Run from repo root:

```bash
npm install
npm run build
npm run lint
npm run format
```

When startup flow or renderer wiring changes, also run:

```bash
npm run verify-startup
```

## References

- Guardrail summary: `references/guardrails.md`
