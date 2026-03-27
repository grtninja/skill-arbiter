# Empirical Mode Routing Telemetry

This reference turns real Codex usage behavior into a governed routing input for:

- `usage-watcher`
- `skill-cost-credit-governor`
- `local-compute-usage`

## Why this exists

Static spend caps are not enough.

The same operator can show radically different weekly burn depending on:

- task archetype
- reasoning effort
- retry/branching behavior
- whether the session is greenfield creation or steady maintenance

The correct goal is not "lowest spend."

The correct goal is:

- lower failure/chatter for the same work class
- better completion-adjusted progress
- bounded spend escalation only when the task class actually justifies it

## Session fields to capture

Every governed session should capture:

- `task_archetype`
- `mode_profile`
- `reasoning_level`
- `authoritative_cost`
- `burn_pct_delta`
- `credits_per_hour`
- `benchmark_api_equivalent_cost`
- `local_marginal`
- `cloud_equivalent`
- `completed_units`
- `unfinished_units`
- `new_apps_created`
- `failure_count`
- `argument_count`
- `rollback_count`
- `manual_intervention_count`
- `provider`
- `model`
- `route_target`
- `latency_ms`
- `lane_health`

## Task archetypes

Use bounded, reusable labels:

- `greenfield_app`
- `maintenance`
- `debugging`
- `refactor`
- `research`
- `review`
- `ops_recovery`
- `content_pipeline`

## Mode profiles

Use explicit operator/runtime labels:

- `economy`
- `standard`
- `surge`

Record these alongside:

- `reasoning_level`

## Interpretation rules

### 1. Burn shape is not explained by one switch alone

When burn spikes across similar time windows, do not treat that as a pure pricing or model effect.

Also evaluate:

- task class change
- reasoning effort change
- branch count / retries
- greenfield versus incremental work

### 2. Unfinished work can still be productive

Sessions with:

- fewer failures
- fewer arguments
- lower spend
- more unfinished units

may still be higher-value than an expensive burst session.

Do not score unfinished work as zero.

### 3. Greenfield app work can justify surge

`surge` mode is justified when:

- the task is greenfield or breakthrough work
- failure/chatter stay within tolerable bounds
- the outcome materially increases system capability

### 4. Maintenance should default to standard

`standard` should remain the default for:

- repo maintenance
- patching
- architecture follow-through
- chained incremental progress

### 5. Local displacement should be measured, not assumed

Prefer local routing when:

- lane health is good
- latency is acceptable
- `local_marginal` is materially below `cloud_equivalent`

Do not assume every local lane should replace every cloud lane.

## First-pass scoring

Use a completion-adjusted progress score instead of raw spend alone.

Example:

```python
def progress_units(completed_units: float,
                   unfinished_units: float,
                   new_apps_created: float,
                   failures: int) -> float:
    raw = (
        completed_units
        + 0.35 * unfinished_units
        + 2.0 * new_apps_created
        - 0.50 * failures
    )
    return max(raw, 0.1)
```

Example efficiency:

```python
def efficiency_score(authoritative_cost: float,
                     completed_units: float,
                     unfinished_units: float,
                     new_apps_created: float,
                     failures: int) -> float:
    return progress_units(
        completed_units=completed_units,
        unfinished_units=unfinished_units,
        new_apps_created=new_apps_created,
        failures=failures,
    ) / max(authoritative_cost, 0.01)
```

This is not sacred math.
It is a governed starting point.

## Policy implications by skill

### `usage-watcher`

Should classify burn as:

- `surge_use`
- `cruise_use`
- `waste_risk`

instead of only red/yellow/green budget posture.

### `skill-cost-credit-governor`

Should emit not only `allow|warn|throttle|disable`, but also a mode recommendation:

- `default_standard`
- `force_local_if_available`
- `review_before_escalation`

### `local-compute-usage`

Should route local work by lane role, not by a fake "everything local is better" assumption.

Examples:

- local small-model lane for endpoint loop ownership
- heavier local lane for bounded coding/debugging
- remote/local protected host when local marginal cost is better and lane health is good

### Subagent routing

The same telemetry should drive subagent placement:

- prefer healthy local OpenClaw-compatible subagents first
- keep cloud subagents on cheap, lower-reasoning sidecar work by default
- preserve premium reasoning budget for the main lane
- treat the user's selected mode as authoritative even when telemetry would recommend a cheaper mix

## Operating rule

Default to:

- `standard`
- bounded local-first routing
- local subagents first
- cheap, lower-reasoning cloud sidecars only when local capacity is unavailable or saturated

Escalate to:

- `surge`
- heavier reasoning
- explicitly approved heavier cloud sidecars

only when the task class and observed outcome justify it.
