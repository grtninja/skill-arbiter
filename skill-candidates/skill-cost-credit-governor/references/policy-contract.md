# Policy Contract

## Analysis Output Keys

- `window`
- `totals`
- `budgets`
- `skills[]`
- `chatter_pairs[]`
- `loop_events[]`
- `policy`

## Per-Skill Row Shape

- `skill`
- `invocations`
- `credits`
- `credits_share_percent`
- `tokens`
- `tokens_per_invocation`
- `avg_runtime_ms`
- `p95_runtime_ms`
- `avg_daily_credits`
- `peak_daily_credits`
- `status_counts`
- `reason_codes`
- `proposed_action`

## Policy Output Shape (`decide`)

- `global_action`
- `actions[]`
- `enforced_at`
- `source_analysis`

`actions[]` items:

- `skill`
- `action`
- `reason_codes`

## Reason Codes

- `cost_spike`
- `inefficient_loop`
- `agent_chatter`
- `runtime_p95_high`
- `high_spend_share`
