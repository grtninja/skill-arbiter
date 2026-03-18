# Bounded Pipeline Role Contract

Wave 1 owner: `skill-arbiter`

This repo participates in the private OpenJarvis-style rollout as a bounded
governance and learning engine.

## Formal bounded roles

### `scheduler`

- may assign slices to lanes using declared budgets
- may not fabricate engine capabilities

### `slice_critic`

- may review completed slices and flag failures
- may not auto-promote new baselines

### `mx3_qc`

- may consume MX3 QC signals and fold them into decisions
- may not claim creative ownership over the media result

### `archive_steward`

- may move stale failures into archive lanes
- may not delete approved baselines automatically

### `tuner`

- may adjust one bounded parameter at a time and queue guarded retries
- may not mutate accepted baselines silently

## Trust and promotion limits

- guarded auto-tune may auto-rank and auto-retry
- baseline promotion remains operator-visible and bounded
- destructive cleanup remains operator-confirmed
- learning evidence must be additive and attributable
