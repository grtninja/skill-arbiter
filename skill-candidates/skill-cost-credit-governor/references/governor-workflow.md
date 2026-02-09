# Governor Workflow

## Inputs

Provide one event row per skill invocation with these preferred fields:

- `timestamp`
- `skill`
- `caller_skill` (optional)
- `prompt_tokens`
- `completion_tokens`
- `total_tokens` (optional)
- `credits` (optional)
- `runtime_ms` (optional)
- `status` (optional)

If `credits` is missing, use `--credits-per-1k-tokens`.

## Core Steps

1. Analyze a rolling window (`--window-days`) to compute per-skill spend and runtime profiles.
2. Detect anomalies:
   - spend spikes
   - repeated caller->skill loops
   - high-frequency low-value caller->skill chatter
   - runtime p95 threshold breaches
3. Derive a global pressure level from daily/window budgets.
4. Emit policy actions per skill.

## Action Semantics

- `ok`: no action required.
- `warn`: require explicit confirmation before high-cost runs.
- `throttle`: restrict scope/frequency until next analysis window.
- `disable`: block non-emergency use until review.

## Evidence Artifacts

- Analysis JSON (`analyze --json-out ...`)
- Policy JSON (`decide --json-out ...`)

Store artifacts with timestamps to compare trend deltas across weekly reviews.
