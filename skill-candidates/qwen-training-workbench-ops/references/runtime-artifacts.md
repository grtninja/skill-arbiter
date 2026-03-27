# Runtime Artifacts

## Dataset Factory

- `penny_training_loop.nsf_expanded.selection.json`
  - what was selected
- `_training_batches/batch_XXX.weighted.json`
  - pre-enrichment slice
- `_training_batches/batch_XXX.enriched.json`
  - enriched slice
- `_training_batches/batch_XXX.export.json`
  - trainable multimodal examples
- `_training_batches/batch_XXX.teacher.json`
  - Huihui teacher outputs for that slice
- `penny_descriptor_finetune.teacher_merged.nsf_expanded.local.json`
  - merged dataset output used by continuation training

## Continuation Training

- `batch_XXX/input.json`
  - exact records used for that batch
- `batch_XXX/batch_sources.json`
  - exact original source refs
- `batch_XXX/trainer.report.json`
  - training metrics
- `batch_XXX/checkpoint.eval.json`
  - checkpoint self-test results
- `batch_XXX/adapter/`
  - saved adapter for carry-forward or eval
