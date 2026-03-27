# Ops Checklist

## Preflight

1. Confirm the machine is not in `media_workbench` mode.
2. Confirm `9041` is reachable.
3. Confirm Huihui is visible in `lms ps --json`.
4. Confirm the expected local student and embedding lanes are reachable on `2234` and `2236`.

## Dataset Factory

Healthy signs:

- selection JSON exists
- `_training_batches` is gaining newer `weighted/enriched/export/teacher` files
- the active worker CPU continues to climb
- Huihui toggles between `idle` and `generating`

Recovery signs:

- the active job has an exit code
- the merged dataset artifact is missing after the job ends
- stderr contains a real runtime exception instead of warnings only

## Continuation Batches

Healthy signs:

- batch directories appear under `evidence/training_runs/.../batch_*`
- each finished batch contains:
  - `input.json`
  - `batch_sources.json`
  - `batch_sources.txt`
  - `trainer.local.json`
  - `trainer.report.json`
  - `checkpoint.eval.json`
  - `adapter/`

## Queue Discipline

Continuation should run only after dataset success, not merely after dataset exit.

If a predecessor failed:

1. stop automated continuation
2. inspect dataset logs and artifacts
3. repair the dataset lane first
