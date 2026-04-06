---
name: vrm-sandbox-startup-acceptance
description: Validate and repair VRM Sandbox startup acceptance with shim-first local model authority, frontend/backend bring-up, and avatar-runtime launch proof. Use when launch behavior, chat handoff, voice fallback, or runtime bridge acceptance must be verified end to end.
---

# VRM Sandbox Startup Acceptance

Use this skill for repo-D-specific startup acceptance and launch preflight.

## Workflow

1. Run local preflight for the VRM Sandbox workspace and loopback model planes.
2. Identify the canonical start/stop flow for the desktop shell and supporting services.
3. Clear stale repo-owned windows and listeners before relaunch.
4. Launch through the canonical accepted path and verify:
   - frontend plus backend together
   - no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows
   - shim-first chat/runtime handoff stays intact
   - state restore and overlay behavior remain correct
5. Validate avatar runtime and chat/voice bridge surfaces after launch.
6. Mark the pass undone if any acceptance gate still fails.

## Required Evidence

- startup command used
- preflight result for `9000` and `2337`
- frontend window proof
- backend/runtime health proof
- note of chat, voice, or overlay failures that remain

## Guardrails

- Treat `:9000` and `:2337` as authoritative.
- Treat `:1234` only as an operator surface when present.
- Do not claim launch success from backend health alone.
- Do not accept a startup path that flashes an empty shell window.

## Best-Fit Companion Skills

- `$desktop-startup-acceptance`
- `$repo-d-setup-diagnostics`
- `$repo-d-ui-guardrails`
- `$local-compute-usage`

## Scope Boundary

Use this skill for VRM Sandbox startup and launch acceptance only.

For deeper avatar-material or round-trip issues, route to the more specific VRM skills.
