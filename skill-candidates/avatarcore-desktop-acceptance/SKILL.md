---
name: avatarcore-desktop-acceptance
description: Enforce AvatarCore workstation desktop-launch acceptance when frontend/backend launcher ownership, stale-window cleanup, and health proof must be explicit. Use when backend-only startup is being mistaken for app readiness or when a combined launcher is being introduced or repaired.
---

# AvatarCore Desktop Acceptance

Use this skill for AvatarCore workstation launch acceptance, not for generic proxy-only validation.

## Workflow

1. Read the target repo `AGENTS.md` and runtime docs first.
2. Do not treat backend-only proxy startup as desktop success on this workstation.
3. Require an explicit combined frontend-plus-backend launcher. If it does not exist yet, report the lane as undone.
4. Validate desktop acceptance gates:
   - no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows remain open after launch
   - no stale repo-owned AvatarCore windows remain before relaunch
   - the visible frontend and required local backend start together
   - `/health` exposes a sanitized readiness snapshot the operator can verify
5. When display or frontend readiness is part of the lane, keep launcher behavior, health reporting, and display/runtime docs aligned.
6. If acceptance changes, update launcher docs, startup checks, and nearby repo guidance in the same pass.

## Required Evidence

- launcher path used
- stale-window cleanup result
- visible frontend proof
- backend health proof
- explicit note if the repo still lacks a valid combined launcher

## Guardrails

- Backend-only `dev` or proxy launch paths are diagnostics, not workstation acceptance.
- Do not claim app readiness if the visible frontend and local backend are not coupled.
- Keep health output sanitized and operator-readable.
- Keep host-specific display or machine assumptions out of repo-tracked public-shape docs.

## Best-Fit Companion Skills

- `$desktop-startup-acceptance`
- `$repo-b-avatarcore-ops`
- `$local-compute-usage`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for AvatarCore desktop-launch acceptance and launcher ownership.

Do not use it for:

1. generic provider-routing changes without launcher impact
2. Unreal content work that does not affect workstation acceptance
3. cross-app meta-harness alignment by itself

## References

- `references/desktop-acceptance-checklist.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. capture the missing launcher or failing acceptance gate
2. route back through `$skill-hub` for chain recalculation
3. resume only after the updated chain returns a deterministic workstation-acceptance next step
