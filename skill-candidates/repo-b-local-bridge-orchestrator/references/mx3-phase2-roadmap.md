# MX3 Phase 2 Roadmap

Phase 1 is local GPU and fail-closed only. MX3 integration is deferred until the baseline pipeline is stable.

## Gate to Start Phase 2

All of the following should be true for at least two weeks of pilot data:

1. Validation pass rate is stable.
2. Median orchestrator runtime meets local SLA targets.
3. Bridge and index failures are controlled and diagnosable.
4. Credit spend shows sustained reduction against baseline.

## Phase 2 Design Targets

1. Introduce a pluggable accelerator adapter interface.
2. Start with embedding or rerank acceleration only.
3. Keep reasoning and policy gates unchanged.
4. Preserve fail-closed behavior and read-only bridge mode.
5. Keep cloud fallback disabled by default.

## Required Safety Checks

1. Explicit capability probe for accelerator readiness.
2. Deterministic fallback to current local GPU path when MX3 adapter fails.
3. Side-by-side quality and latency comparison on a fixed benchmark set.
4. No change to path authorization and evidence contracts.

## Non-Goals

- Do not route all inference through MX3 in first integration step.
- Do not loosen confidence/evidence thresholds to chase throughput.
- Do not enable write-capable bridge tasks.
