---
name: catalog-snapshot-consistency
description: Keep generated catalogs, operator snapshots, and documented summaries aligned after workflow or command-surface changes. Use when visible command matrices, media/staging catalogs, or skill/status summaries drift from the runtime or generated source of truth.
---

# Catalog Snapshot Consistency

Use this skill when a repo has both generated/operator-facing snapshots and a runtime or source-of-truth surface that can drift.

## Workflow

1. Identify the canonical source of truth before editing any snapshot or catalog.
2. List every downstream artifact that presents the same information:
   - generated catalogs
   - operator summaries
   - command matrices
   - status or alignment snapshots
3. Update the authoritative source first, then regenerate or reconcile the derived artifacts.
4. Compare the refreshed outputs against the runtime behavior or current command surface.
5. Record any intentional mismatch as an explicit limitation instead of leaving silent drift.

## Required Evidence

- authoritative source file or runtime surface identified
- regenerated or refreshed snapshot/catalog artifact
- note of what changed in the downstream presentation
- confirmation that no stale snapshot remains in the touched lane

## Guardrails

- Do not hand-edit generated artifacts when a deterministic generator exists.
- Do not treat an operator snapshot as authoritative if runtime truth disagrees.
- Keep privacy-sensitive host details out of generated summaries.
- Fail closed if you cannot prove which artifact is canonical.

## Best-Fit Companion Skills

- `$docs-alignment-lock`
- `$skill-common-sense-engineering`
- `$media-staging-prompthead-ops`
- `$shockwave-voice-command-governance`

## Scope Boundary

Use this skill only for authoritative-source versus snapshot/catalog consistency work.

For runtime behavior fixes, route through the most specific runtime or repo skill first and return here only to reconcile the derived artifacts.
