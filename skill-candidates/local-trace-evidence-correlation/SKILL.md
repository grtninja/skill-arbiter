---
name: local-trace-evidence-correlation
description: Correlate local decision telemetry, trace recording, and emitted evidence across STARFRAME services. Use when arbiter, media, dashboard, or embodiment traces need to line up as one operator-readable storyline.
---

# Local Trace Evidence Correlation

Use this skill when multiple local repos emit trace or telemetry artifacts for the same workflow.

## Workflow

1. Identify the candidate-generation, telemetry, ranking, trace, and emission surfaces involved.
2. Collect the minimal trace artifacts needed from each repo.
3. Normalize timestamps, request IDs, and operator-visible identifiers where possible.
4. Call out any missing hop that prevents end-to-end correlation.
5. Produce one clear evidence chain before closing.

## Required Evidence

- the repos or services correlated
- the trace or telemetry artifacts used
- the shared identifiers or timing anchors
- any missing hop or broken link in the evidence chain

## Guardrails

- Do not claim end-to-end traceability if one hop is missing.
- Prefer bounded metadata over raw payload copying.
- Keep private content out of the correlated summary.
- Fail closed if trace and operator-visible state disagree.

## Best-Fit Companion Skills

- `$heterogeneous-stack-validation`
- `$repo-c-trace-ndjson-validate`
- `$repo-a-telemetry-kv-guard`
- `$skill-enforcer`

## Scope Boundary

Use this skill only for cross-repo trace and telemetry correlation.

For schema-level trace validation inside one repo, route to the more specific trace skill for that repo.
