# Optimizer Workflow

## Inputs

Preferred execution log fields:

- `timestamp`
- `skill`
- `duration_ms`
- `cold_start` (optional)
- `cache_hit` (optional)
- `status` (optional)

If cold/warm labels are missing, the first invocation per skill in-window is treated as cold.

## Analysis Outputs

- per-skill cold/warm p50 and p95
- cold penalty (`cold_p50 - warm_p50`)
- prewarm candidate ranking
- never-auto-invoke candidates for rare expensive skills

## Plan Outputs

- ordered prewarm steps
- disable-auto-invoke steps
- source analysis linkage for auditability
