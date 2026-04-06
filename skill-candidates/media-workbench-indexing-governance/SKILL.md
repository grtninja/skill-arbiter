---
name: media-workbench-indexing-governance
description: Govern Media Workbench indexing posture across metadata-only baselines, opt-in content-derived indexing, local manifest storage, and operator-facing index summaries. Use when indexing tools, manifests, catalog DBs, or media-root governance change together.
---

# Media Workbench Indexing Governance

Use this skill for Media Workbench indexing policy and local-catalog governance.

## Workflow

1. Confirm the current indexing posture before mutation:
   - metadata-only by default
   - content-derived indexing only by direct opt-in
   - derived artifacts stay inside the workspace
2. Inspect the indexing stack together:
   - media-root configs
   - metadata-summary generation
   - reference-catalog builders and validation
   - operator-facing summary or catalog surfaces
3. Keep manifests, catalogs, and policy docs aligned when indexing behavior changes.
4. Re-run the relevant index or catalog validation path before closing.
5. Report whether the repo still preserves `metadata_only` as the default truth.

## Required Evidence

- indexing mode used
- affected config, manifest, or catalog path
- validation output for the changed indexing surface
- note of any opt-in content-derived behavior introduced or preserved

## Guardrails

- Do not mutate the private media root to satisfy indexing.
- Do not enable captioning, embeddings, OCR, or face workflows silently.
- Keep derived indexes, manifests, and notes inside the workspace.
- If indexing policy and operator-facing summaries disagree, report the lane as unresolved.

## Best-Fit Companion Skills

- `$media-workbench-worker-contracts`
- `$local-compute-usage`
- `$docs-alignment-lock`
- `$skill-common-sense-engineering`

## Scope Boundary

Use this skill only for Media Workbench indexing posture, catalog governance, and validation.

For render-pipeline or worker contract work, route through the more specific media-workbench skills.
