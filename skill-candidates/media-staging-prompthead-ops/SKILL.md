---
name: media-staging-prompthead-ops
description: Operate Media Workbench source staging, prompt-head generation order, lane assignment, and resume-safe draft continuity as one workflow surface. Use when staging, previews, or generation-order logic change together.
---

# Media Staging Prompthead Ops

Use this skill for the front half of the Media Workbench operator flow.

## Workflow

1. Inspect staging, prompt-head, queue submission, and preview surfaces together.
2. Keep generation order explicit across the staged render lanes.
3. Preserve draft state and resumable work-item continuity during refresh or restart.
4. Ensure preview, branch state, and blocking reason remain operator-visible.
5. Re-run a bounded staging-to-queue proof before closing.

## Required Evidence

- staging or prompt-head surface touched
- lane assignment or generation-order rule touched
- resume or draft-state behavior checked
- preview or blocking-reason truth checked after the change

## Guardrails

- Do not hide active staged work on refresh.
- Do not let prompt-head logic silently bypass lane-order rules.
- Keep preview and blocking state operator-visible.
- Fail closed if staging state and queued work disagree.

## Best-Fit Companion Skills

- `$media-workbench-desktop-ops`
- `$media-workbench-worker-contracts`
- `$catalog-snapshot-consistency`
- `$desktop-startup-acceptance`

## Scope Boundary

Use this skill only for Media Workbench staging, prompt-head ordering, and resume-safe operator flow.

For indexing or QC/refinement behavior, route through the more specific media skills.
