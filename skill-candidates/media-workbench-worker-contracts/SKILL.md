---
name: "media-workbench-worker-contracts"
description: "Guard the STARFRAME Media Workbench worker ownership contract, queue/work-item lifecycle, and desktop-to-worker status surfaces. Use when changes touch `9040`, job payloads, resumable work items, operator snapshots, or worker-facing docs/tests."
metadata:
  author: "grtninja"
  canonical_source: "https://github.com/grtninja/skill-arbiter"
---

# Media Workbench Worker Contracts

Use this skill when the Media Workbench `9040` worker contract changes and the desktop shell, queue lifecycle, and operator-visible state all need to stay aligned.

## Workflow

1. Read the target repo `AGENTS.md` and the operator app contract first.
2. Treat the repo as the sole owner of the `9040` worker contract, local dashboard, and thin desktop shell.
3. Inspect these worker surfaces together:
   - `/health`
   - `/ready`
   - `/v1/media-agent/status`
   - `/v1/media-agent/jobs`
   - `/v1/media-agent/summary`
4. Preserve operator-visible workflow state:
   - `active_job_id`
   - queue depth and tracked jobs
   - resumable work item target
   - draft state continuity
   - output/artifact visibility
5. Validate desktop-to-worker coupling:
   - healthy worker reuse when already up
   - repo-owned bootstrap when down
   - queue, cancel, retry, and resume-latest routes stay consistent
   - runtime snapshot and operator snapshot still describe the same active systems
6. When job payloads or status fields change, update Electron IPC, docs, and tests in the same pass.
7. Distinguish review blockers from worker crashes:
   - a structured QC or promotion `not ready` result is an operator-visible review state, not an automatic failed-generation retry
   - preserve the summary, next action, and blocker evidence in worker-visible state instead of collapsing them into a generic crash reason
8. Treat `9041` and other heavy media-worker lanes as exclusive resources:
   - do not dispatch a second heavy generation, refine, or upscale job while a tracked `9041` job is active or the queue is saturated
   - surface backpressure as `queued`, `busy`, or `not ready`, never as a silent timeout or hidden retry
   - retries must have explicit max attempts, bounded request timeouts, and backoff before they can re-enter the queue

## Required Evidence

- worker health and ready proof
- current status or summary payload
- queue or work-item lifecycle proof for the changed path
- heavy-lane availability or backpressure proof when touching generation, refine, upscale, or QC routes
- note of any operator-visible field that changed
- exact docs/tests updated with the contract change

## Guardrails

- Sister repos may submit work through the worker, but they do not redefine the contract.
- Do not hide or silently reset active job, draft, or resume state.
- Do not treat `9041` timeout/backpressure as permission to submit another job blindly.
- Do not refine, polish, upscale, or promote still-image outputs that have not passed the current QC gate.
- Keep source-by-reference behavior intact; do not duplicate the source library to satisfy the UI.
- If worker health, queue lifecycle, or resume semantics are ambiguous, fail closed and report the contract as unresolved.

## Best-Fit Companion Skills

- `$media-workbench-desktop-ops`
- `$local-compute-usage`
- `$docs-alignment-lock`
- `$skill-common-sense-engineering`

## Scope Boundary

Use this skill only for the Media Workbench worker contract and its desktop/operator coupling.

Do not use it for:

1. generic Comfy workflow tuning without contract changes
2. full training-workbench tasks
3. VRM or avatar runtime work

## References

- `references/worker-contract-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. capture the failing worker route or status field
2. route back through `$skill-hub` for chain recalculation
3. resume only after the updated chain returns a deterministic contract fix path
