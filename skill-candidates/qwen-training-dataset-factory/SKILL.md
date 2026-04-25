---
name: "qwen-training-dataset-factory"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Build, enrich, distill, and validate local training datasets for the Qwen Training Workbench. Use when dataset export, weighted-study assembly, label distillation, workstation-mode enforcement, or training-input validation change together."
---

# Qwen Training Dataset Factory

Use this skill for the data-prep lane behind local Qwen teacher-student training work.

## Trigger Conditions

Use this skill when the work involves one or more of:

- exporting source material into training-ready datasets
- enriching media manifests or study metadata
- distilling labels from prior model output
- weighting or filtering training studies
- validating dataset inputs before batch or staggered training runs

Route elsewhere when:

- the work is about running or resuming training jobs: use `$qwen-training-workbench-ops`
- the work is about checkpoint comparison or eval behavior: use `$qwen-training-checkpoint-eval`
- the work is about desktop shell behavior only: use `$qwen-training-desktop-ops`

## Workflow

1. Identify the dataset source surfaces and output artifacts.
2. Capture the workstation mode and any local-only constraints before mutation.
3. Run or update the data-factory stages in order:
   - export
   - enrich
   - distill
   - weight/filter
   - validate
4. Keep intermediate manifests deterministic and resumable.
5. Verify the resulting dataset contract against the intended training lane.
6. Record what changed in the dataset schema, study weights, or label provenance.

## Required Evidence

- input source paths or manifest identifiers
- output dataset/manifests produced
- validation command or test evidence
- workstation-mode assumptions used during the build
- any skipped or manually reviewed examples

## Guardrails

- Do not mix unrelated experimental transforms into the same dataset pass.
- Keep provenance explicit for generated labels and enriched metadata.
- Fail closed when workstation mode, dataset schema, or output directories drift from the expected lane.
- Treat training-input validation as required, not optional cleanup.

## Scope Boundary

Use this skill for dataset-factory preparation and validation only.

Do not use it for long-running training execution, desktop shell fixes, or checkpoint evaluation.

## References

- `$qwen-training-workbench-ops`
- `$qwen-training-checkpoint-eval`
- `$local-compute-usage`
