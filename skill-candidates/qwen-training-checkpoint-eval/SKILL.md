---
name: qwen-training-checkpoint-eval
description: Evaluate saved Qwen training checkpoints against batch-aligned training samples and trained-adapter eval lanes. Use when inspecting checkpoint.eval.json, validating a saved batch adapter on the Radeon eval lane, or comparing baseline student behavior against a newly trained checkpoint before promotion.
---

# Qwen Training Checkpoint Eval

Use this skill for logical checkpoint testing during or after staggered student training.

## Workflow

1. Start with the saved batch artifacts, not a live guess.
2. Read `checkpoint.eval.json` and `trainer.report.json` for the batch.
3. Verify exact source refs in `batch_sources.json` or `batch_sources.txt`.
4. If deeper validation is needed, point the Radeon eval lane at the saved adapter and verify it loads.
5. Compare the trained checkpoint against the baseline student only after the adapter-loaded eval lane is healthy.

## Canonical Checks

Batch artifact review:

```bash
type <batch-dir>\checkpoint.eval.json
type <batch-dir>\trainer.report.json
type <batch-dir>\batch_sources.json
```

Eval lane launch:

```powershell
powershell -ExecutionPolicy Bypass -File `
  <training-workbench-root>\tools\start_qwen35_4b_radeon_eval.ps1 `
  -Config <eval-config-pointing-at-batch-adapter>
```

Eval lane health:

```bash
curl <loopback-eval-lane>/health
curl <loopback-eval-lane>/v1/models
```

## Pass Criteria

At minimum, require:

1. `checkpoint.eval.json` exists
2. the eval JSON parsed at least one sample response successfully
3. `adult_context` and `penny_affinity` matches are present for the sampled records
4. `/health` shows `adapter_loaded = true` when a saved adapter is mounted on the eval lane

## Scope Boundary

Use this skill for checkpoint validation and trained-adapter smoke testing.

Do not use this skill for:

1. Running the full dataset factory
2. Long-running training supervision
3. LM Studio teacher recovery

## References

- `references/checkpoint-contract.md`
