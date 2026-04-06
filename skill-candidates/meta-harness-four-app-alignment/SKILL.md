---
name: meta-harness-four-app-alignment
description: Align the four core local app surfaces under the shared meta-harness contract. Use when PC Control, shim/control-center, STARFRAME app, and avatar-runtime defaults or docs drift on model authority, canonical repo root, continuity, or endpoint expectations and one coordinated pass must repair them together.
---

# Meta-Harness Four-App Alignment

Use this skill when one pass must align the four core local app surfaces as a single contract:

- PC Control governance surface
- shim/control-center surface
- STARFRAME app surface
- avatar runtime surface

## Workflow

1. Route the work through `$skill-hub`.
2. Capture first-party evidence before edits:
   - PC Control local-agent or status-surface evidence
   - authoritative model-lane health on `:9000` and `:2337`
   - avatar runtime health if it is expected to be live
3. Normalize the active contract:
   - canonical repo root is `G:\GitHub`
   - `http://127.0.0.1:9000/v1` is the public authoritative lane
   - `http://127.0.0.1:2337/v1` is the hosted large-model authoritative lane
   - `http://127.0.0.1:1234/v1` and LM Studio loaded-models surfaces are non-authoritative operator surfaces only
4. Review open diffs and contract/docs drift across the four surfaces before patching.
5. Repair the smallest authoritative layer first:
   - governance/control contracts
   - shim/router defaults
   - STARFRAME app continuity/defaults
   - avatar runtime defaults and health expectations
6. Validate each surface with targeted health, docs-lockstep, and repo-gate evidence.
7. Record remaining gaps and route follow-on fixes to the most specific skill lanes.

## Required Evidence

- PC Control evidence or status-surface output
- endpoint/status results for `9000`, `2337`, and any expected runtime lane
- exact repo/file list for each aligned surface
- targeted validation output per touched surface
- explicit list of any remaining degraded lanes

## Route To Supporting Skills

- `$shim-pc-control-brain-routing` for one-brain routing and port-authority fixes
- `$heterogeneous-stack-validation` for end-to-end runtime truth checks
- `$docs-alignment-lock` for cross-repo documentation lockstep
- `$skill-enforcer` when boundary/policy synchronization is required
- `$desktop-startup-acceptance` when launcher or startup behavior changed

## Scope Boundary

Use this skill for coordinated four-surface contract alignment only.

Do not use it for:

1. isolated single-repo fixes already covered by a more specific repo skill
2. release-version bumping without contract/runtime review
3. generic workstation bring-up unrelated to the four-surface meta-harness lane

## References

- `references/alignment-contract.md`

## Loopback

If one surface remains unresolved:

1. capture the failing contract slice with exact evidence
2. route the failing slice to the smallest specific skill
3. resume this four-app lane only after the blocking slice is repaired
