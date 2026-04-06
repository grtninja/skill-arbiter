---
name: dataset-provenance-manifest-governance
description: Keep local training dataset provenance, merged outputs, and manifest truth aligned across dataset-building repos. Use when teacher distillation, enrichment exports, or study manifests change together.
---

# Dataset Provenance Manifest Governance

Use this skill when the Penny training-data chain changes across Qwen Training and Media Workbench surfaces.

## Workflow

1. Identify the source manifests, merged outputs, and derived dataset artifacts involved.
2. Confirm provenance rules before changing batch assembly or export paths.
3. Keep teacher, student, and enrichment stages legible in the manifest chain.
4. Re-run the relevant validation or export proof after updates.
5. Record whether the dataset remains local-only and reproducible.

## Required Evidence

- source manifest or config touched
- derived dataset artifact or export touched
- provenance rule or weighting rule preserved
- validation or export proof for the changed path

## Guardrails

- Do not collapse teacher, enrichment, and student stages into one opaque artifact.
- Keep local-only provenance explicit.
- Do not silently rewrite upstream source media or manifests.
- Fail closed if the manifest chain no longer explains the output.

## Best-Fit Companion Skills

- `$qwen-training-dataset-factory`
- `$qwen-training-campaign-ops`
- `$media-workbench-indexing-governance`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for dataset provenance, manifest lineage, and derived training-artifact governance.

For checkpoint evaluation or fine-tune execution, route through the more specific training skills.
