---
name: "qwen-training-workbench-ops"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate the local teacher-student Qwen training workbench for long-running dataset-factory, staggered continuation batches, and training-agent supervision. Use when advancing or monitoring the private Huihui-to-Qwen3.5-4B pipeline, switching workstation modes, checking batch artifacts, or resuming overnight local training without media-workbench contention."
---

# Qwen Training Workbench Ops

Use this skill for the private local training workbench that feeds the media stack.

## Workflow

1. Confirm the workstation is in the correct local mode before touching the lane.
2. Identify whether the active step is dataset factory or staggered continuation.
3. Check the long-running training supervisor on `127.0.0.1:9041` before starting or resuming work.
4. Validate the required local model lanes:
   - teacher lane on a loopback-hosted OpenAI-compatible runtime
   - baseline student lane on a loopback-hosted OpenAI-compatible runtime
   - embedding lane on a loopback-hosted OpenAI-compatible runtime
5. Use artifact progress, not guesswork, to decide whether to continue, wait, or recover.
6. If the dataset lane fails, inspect logs and artifacts before any continuation batch is allowed to run.

## Phase Routing

Use `dataset_factory` when the goal is to build or expand the distilled teacher-student dataset:

- weighted Penny-first selection
- Huihui teacher distillation
- MX3 and embedding enrichment
- merged dataset artifact production

Use `nsf_staggered_batches` when the goal is to keep training the student forward in microbatches:

- batch-level adapter carry-forward
- per-batch `trainer.report.json`
- per-batch `checkpoint.eval.json`
- exact source refs in `batch_sources.json` and `batch_sources.txt`

Do not use this skill for:

1. Media rendering/export work. Use the media-workbench lane instead.
2. Generic LM Studio troubleshooting without training-workbench context.
3. Publishing or pushing model artifacts. This lane is private local only.

## Canonical Commands

Supervisor status:

```bash
curl http://127.0.0.1:9041/v1/training-agent/status
curl http://127.0.0.1:9041/v1/training-agent/jobs/<job_id>
```

Dataset factory launch:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\start_penny_dataset_factory_nsf_expanded.ps1
```

Continuation batch launch:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\start_qwen35_4b_radeon_nsf_staggered.ps1
```

LM Studio teacher check:

```bash
lms ps --json
```

## Artifact Checks

Prefer these artifacts as the source of truth:

- `evidence/training_datasets/penny_training_loop.nsf_expanded.selection.json`
- `evidence/training_datasets/_training_batches/*.weighted.json`
- `evidence/training_datasets/_training_batches/*.enriched.json`
- `evidence/training_datasets/_training_batches/*.export.json`
- `evidence/training_datasets/_training_batches/*.teacher.json`
- `evidence/training_datasets/penny_descriptor_finetune.teacher_merged.nsf_expanded.local.json`
- `evidence/training_runs/qwen35_4b_radeon_nsf_expanded_staggered/*`

If the selection artifact is stale but `_training_batches` continues to advance, treat the run as healthy and still in progress.

## Loopback

If the lane stalls or becomes ambiguous:

1. Capture the active job JSON from `9041`.
2. Capture the most recent batch artifact timestamps.
3. Capture `lms ps --json`.
4. Resume only after the next action is deterministic: `wait`, `recover dataset`, `resume continuation`, or `inspect failure logs`.

## References

- `references/ops-checklist.md`
- `references/runtime-artifacts.md`
