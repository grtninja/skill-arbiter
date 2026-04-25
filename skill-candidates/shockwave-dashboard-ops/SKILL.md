---
name: "shockwave-dashboard-ops"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate and debug the Shockwave dashboard/router lane when shim-first model routing, startup contracts, tool-bridge behavior, and operator handoff must stay aligned. Use when recent dashboard work touches startup verification, bridge services, authority metadata, or router-facing docs."
---

# Shockwave Dashboard Ops

Use this skill for the Shockwave dashboard/router surface.

## Workflow

1. Confirm the current startup contract and operator-facing launcher path.
2. Verify shim-first routing and authority metadata before UI changes:
   - `:9000` public plane
   - `:2337` hosted large-model lane
   - `:1234` operator-only LM Studio surface
3. Inspect dashboard, tool-bridge, and startup-contract files together.
4. Patch UI, bridge, and contract drift in one pass.
5. Re-run startup verification and router/bridge smoke checks before closing.

## Required Evidence

- startup verification output
- dashboard or bridge health result
- exact files changed
- note of any remaining operator handoff or authority drift

## Guardrails

- Do not let direct LM Studio assumptions override shim-first routing.
- Keep dashboard docs and startup verification scripts aligned with shipped behavior.
- Prefer the repo-owned startup contract over ad hoc manual launch paths.

## Best-Fit Companion Skills

- `$desktop-startup-acceptance`
- `$local-compute-usage`
- `$repo-b-thin-waist-routing`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for the Shockwave dashboard/router lane.

If the request expands into broader multi-app alignment, route through `$meta-harness-four-app-alignment`.
