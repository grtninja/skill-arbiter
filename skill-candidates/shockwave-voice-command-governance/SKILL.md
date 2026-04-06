---
name: shockwave-voice-command-governance
description: Maintain Shockwave voice-command parity across parser order, source-aware filtering, touch-surface analogs, and missing driving-command gaps. Use when voice command behavior and dashboard controls drift together.
---

# Shockwave Voice Command Governance

Use this skill for Project Shockwave's voice-command matrix and surface-parity lane.

## Workflow

1. Start from the current command matrix, not from ad hoc parser guesses.
2. Compare parser order, direct fast paths, and JSON fallback behavior to the visible UI controls.
3. Keep source-aware command filtering explicit for music, radio, maps, camera, telemetry, and memory.
4. Track missing command families as deliberate gaps rather than hidden regressions.
5. Re-run a bounded voice-command parity proof after updates.

## Required Evidence

- command family touched
- parser or UI surface touched
- source-aware filtering rule checked
- parity or missing-gap note after the change

## Guardrails

- Do not expose voice commands that the active source cannot honor.
- Do not leave touch-only controls undocumented if they should have voice analogs.
- Keep radio and music handoff explicit.
- Fail closed if parser order creates ambiguous or unsafe command capture.

## Best-Fit Companion Skills

- `$shockwave-dashboard-ops`
- `$distributed-voice-plane-governance`
- `$catalog-snapshot-consistency`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for Shockwave voice command parity and command-surface governance.

For startup or dashboard shell behavior alone, route through `$shockwave-dashboard-ops`.
