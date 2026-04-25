---
name: "desktop-startup-acceptance"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Enforce explicit desktop startup acceptance across local app repos. Use when normalizing Windows app launchers, stale-window cleanup, frontend/backend coupling, state restore, shortcut ownership, or machine-specific app rosters."
---

# Desktop Startup Acceptance

Use this skill for cross-repo desktop startup normalization and validation.

## Workflow

1. Read the target repo `AGENTS.md` and any startup/runbook docs first.
2. Confirm whether the app belongs on the target machine before launching it.
3. Identify the canonical repo-owned start and stop commands.
4. Close stale repo-owned windows, listeners, and processes before relaunch.
5. Launch only through the canonical visible path.
6. Validate acceptance gates:
   - no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows
   - no relaunch over stale app windows
   - frontend plus backend together for desktop apps
   - user state restore remains intact (window/layout/profile/settings)
   - shortcuts/icons point at the current repo-owned launcher, not stale packaged paths
7. If any gate fails, report the app as undone instead of claiming the startup is fixed.

## Canonical Evidence

- startup command used
- stale-process cleanup evidence
- frontend window proof
- backend health proof
- shortcut target/icon proof
- explicit list of any remaining acceptance failures

## Scope Boundary

Use this skill only for desktop startup/restart acceptance and launcher normalization.

Do not use it for:

1. USB export reconciliation.
2. Deep hardware-runtime root cause work.
3. General docs-only lockstep updates.

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the failing launcher path and missing acceptance gate.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
