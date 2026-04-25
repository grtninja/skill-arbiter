---
name: "qwen-training-campaign-ops"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate the Qwen Training Workbench campaign lane across `9041` worker queue ownership, named campaign catalogs, dependency-aware job expansion, and restart-safe continuation semantics. Use when campaign configs, worker APIs, or continuation scheduling change together."
---

# Qwen Training Campaign Ops

Use this skill for named campaign and queue orchestration in the Qwen Training Workbench.

## Workflow

1. Treat the `9041` worker as the sole owner of training queue and campaign semantics.
2. Inspect campaign behavior across these surfaces together:
   - campaign catalog config
   - worker API contract
   - campaign launcher
   - dependency-aware job expansion
   - restart, retry, cancel, and recovery behavior
3. Keep dataset phases and continuation batches ordered so failed prerequisites do not silently advance.
4. Prefer named campaigns and worker-owned APIs over ad hoc raw-script orchestration.
5. Re-run worker contract checks or campaign-start proofs before closing.

## Required Evidence

- campaign config or campaign-start payload
- worker route or queue proof
- note of dependency or `requires_success_of` behavior
- restart, retry, or cancel evidence for the changed path

## Guardrails

- Sister repos may submit jobs or campaigns, but they do not redefine queue ownership.
- Do not let failed dataset phases roll into continuation work.
- Keep campaign materialization explicit and dependency-aware.
- Treat raw launchers as local operator/debug tools unless the worker contract owns them.

## Best-Fit Companion Skills

- `$qwen-training-workbench-ops`
- `$qwen-training-dataset-factory`
- `$local-compute-usage`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for Qwen Training Workbench campaign catalogs, worker queue semantics, and continuation orchestration.

For dataset building or checkpoint evaluation alone, route to the more specific training skills.
