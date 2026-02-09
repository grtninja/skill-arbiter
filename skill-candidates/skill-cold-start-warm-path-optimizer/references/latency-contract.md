# Latency Contract

## Analyze Output Keys

- `generated_at`
- `window`
- `thresholds`
- `skills[]`
- `prewarm_candidates[]`
- `never_auto_invoke[]`
- `recommendations[]`

## Skill Row Shape

- `skill`
- `invocations`
- `cold_count`
- `warm_count`
- `cold_p50_ms`
- `cold_p95_ms`
- `warm_p50_ms`
- `warm_p95_ms`
- `cold_penalty_ms`
- `cold_to_warm_ratio`
- `status_counts`

## Plan Output Keys

- `generated_at`
- `source_analysis`
- `max_prewarm`
- `steps[]`

`steps[]` contains:

- `step`
- `skill`
- `action` (`prewarm` | `disable_auto_invoke`)
- `note`
- optional scoring metadata
