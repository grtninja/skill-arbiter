# Cost Control Playbook

## Inputs

Provide usage rows with:

- `Date`
- `Service`
- `Credits used`

When loopback stack evidence is available, also ingest:

- `/health`
- `/api/accounting/summary`

Relevant fields:

- `tpk`
- `authoritative_cost_state`
- `preview_cost_state`
- `displacement_value_preview`
- `benchmark_api_equivalent_cost`
- `local_marginal_cost`
- `cloud_equivalent_cost`
- `savings_vs_cloud_marginal`
- routing/provider and lane-health context

Accepted date examples:

- `2026-02-09`
- `Feb 9, 2026`
- `02/09/2026`

## Operating Modes

1. Economy
   - Scope: triage, diagnostics, and narrow edits.
   - Keep prompts concise and avoid exploratory loops.
2. Standard
   - Scope: normal implementation and verification.
   - Batch related edits before running expensive validation.
3. Surge
   - Scope: only urgent deadlines.
   - Use temporarily and return to standard/economy quickly.

## Spend Reduction Tactics

1. Reuse prior analysis artifacts (`run.json`, generated reports, inventories).
2. Prefer deterministic scripts over repeated back-and-forth prompt probing.
3. Avoid repeated full-repo scans when a bounded query can answer the question.
4. Run expensive checks once per coherent change batch, not after every micro-edit.
5. Pause non-critical work when weekly remaining limit enters red status.
6. If `displacement_value_preview` is positive, shift more work onto local loopback routes before paid-credit or included-limit pressure rises.
7. Treat `authoritative_cost_state` as billing truth and `preview_cost_state` as strategic value. Never confuse the two.

## Rate-Limit Tactics

1. If weekly remaining is red, switch to Economy mode immediately.
2. If 5-hour remaining is yellow/red, queue low-priority work for the next cycle.
3. Keep a reserve budget (`reserve_percent`) for unexpected incidents.
4. If weekly limits recover faster than they deplete while local displacement remains positive, keep the local-first chain active and reassess rather than assuming the bars are arbitrary.
