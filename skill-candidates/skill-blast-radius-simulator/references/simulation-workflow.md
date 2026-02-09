# Simulation Workflow

## Objective

Predict the likely operational impact of a skill before admission.

## Inputs

- Skill root directory
- Candidate skill list
- Optional baseline report from an earlier simulation run
- Acknowledgement threshold (`low`, `medium`, `high`, `critical`)

## Steps

1. Scan SKILL metadata and bundled scripts.
2. Count heuristic signals for destructive commands, shell risks, unbounded scans, network usage, and absolute paths.
3. Compute a risk score and level.
4. Compare against baseline score (if provided).
5. Mark `ack_required=true` for high-risk or high-delta skills.

## Rollout Pattern

- run simulation before arbitration/admission
- review reason codes
- add guardrails or decline skill when high-risk signals remain
