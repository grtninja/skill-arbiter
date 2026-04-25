---
name: "shockwave-operator-handoff"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Preserve Shockwave operator handoff across startup, control-rail contract display, chat/status surfaces, and voice/manual recovery behavior. Use when dashboard changes affect how the operator sees mode, authority, services, playback, or degraded-state transitions."
---

# Shockwave Operator Handoff

Use this skill when Project Shockwave changes affect the operator-facing handoff between startup, live dashboard state, and the typed local control surface.

## Workflow

1. Read the target repo `AGENTS.md`, README, and startup contract first.
2. Confirm the repo-owned visible dashboard path still matches the startup wrapper and shim-first authority model:
   - `:9000` public plane
   - `:2337` hosted large-model lane
   - `:1234` non-authoritative operator surface only
3. Inspect the operator handoff surfaces together:
   - startup verification script and test
   - control rail contract block
   - chat/status strip
   - app-level event/status handling
4. Preserve operator-visible handoff state:
   - current mode and profile
   - control-plane and display-host authority labels
   - active service and phase visibility
   - transcript/tool-card continuity
   - hot-mic and voice-path state
   - interrupted playback resume behavior
5. Keep typed bridge/API payloads aligned with what the dashboard labels and summaries claim.
6. Re-run startup verification and nearby UI/runtime checks before closing.

## Required Evidence

- startup-contract verification output
- operator-facing status snapshot or UI proof
- exact handoff surfaces touched
- note of any remaining degraded-state or authority drift

## Guardrails

- Do not let direct LM Studio assumptions override shim-first authority.
- Do not hide offline, degraded, or disconnected service state behind generic labels.
- Keep the lane read-only with respect to vehicle control and autonomy boundaries.
- If startup proof and dashboard status disagree, report the handoff as unresolved.

## Best-Fit Companion Skills

- `$shockwave-dashboard-ops`
- `$desktop-startup-acceptance`
- `$local-compute-usage`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for Shockwave operator handoff and dashboard-state continuity.

Do not use it for:

1. generic router or provider changes with no operator-surface effect
2. vehicle or hardware integration outside the dashboard handoff
3. full cross-app meta-harness alignment

## References

- `references/operator-handoff-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. capture the failing startup proof or operator-state drift
2. route back through `$skill-hub` for chain recalculation
3. resume only after the updated chain returns a deterministic handoff repair path
