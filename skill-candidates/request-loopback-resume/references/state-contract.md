# Workstream State Contract

## Lane Status Values

- `pending`
- `in_progress`
- `completed`
- `blocked`

## Invariants

1. Exactly zero or one lane may be `in_progress`.
2. Lane names are unique and case-sensitive.
3. `resume` chooses `in_progress` first, then first `pending` lane.
4. `resume` returns:
   - `continue` when an `in_progress` lane exists
   - `start` when no `in_progress` lane exists and a `pending` lane exists
   - `blocked` when only blocked lanes remain unfinished
   - `done` when all lanes are completed

## Evidence Guidance

Capture evidence artifacts whenever a lane transitions to `completed`:

- gate JSON outputs (`arbiter`, `installer`, `audit`)
- validation logs
- generated reports
