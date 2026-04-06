---
name: shim-pc-control-brain-routing
description: Enforce one-brain routing across VRM Sandbox, PC Control, and MemryX shim with shim-first public endpoint authority on port 9000. Use when VRM chat/control behavior must be governed by PC Control without changing the public model-plane endpoint.
---

# Shim PC Control Brain Routing

Use this skill when the operator wants:

- all apps to share one brain lane
- VRM Sandbox to act through PC Control governance
- MemryX shim to remain the public endpoint authority on `http://127.0.0.1:9000`

## Non-Negotiable Contract

1. Public model-plane endpoint stays `9000`.
2. Do not introduce a new public default port for chat routing.
3. Do not switch workstation mode/profile unless explicitly requested.
4. Normalize repo roots to `G:\GitHub`; treat legacy `Documents\GitHub` paths only as aliases to report and correct.
5. Treat the hosted 27B lane on `http://127.0.0.1:2337/v1` as authoritative alongside the shim public plane.
6. Treat `http://127.0.0.1:1234/v1` only as a non-authoritative operator surface when it is present.
7. Do research before edits:
   - PC Control local-agent or status-surface evidence first
   - bounded sub-agents for repo evidence only after first-party evidence is captured

## Mandatory Research Workflow

1. Capture live lane state before edits:
   - `127.0.0.1:9000`
   - `127.0.0.1:2337`
   - `127.0.0.1:1234`
   - `127.0.0.1:8890`
   - `127.0.0.1:5175`
2. Query PC Control local-agent or status evidence first:
   - `GET /v1/agent-fabric/contracts/endpoints`
   - `GET /v1/agent-fabric/models/local`
   - `POST /v1/agent-fabric/local-agent/chat` (research-only prompt)
3. Spawn bounded sub-agents for:
   - PC Control repo endpoint contract and adapter points
   - shim repo route and connector selection path
   - avatar runtime repo OpenAI-compatible request/response expectations
4. Keep local sidecars preferred; if cloud sidecars are unavoidable, keep them lower-reasoning and low-cost.
5. Build a grounded patch plan with file/line references before any implementation.

## Canonical Checks

```powershell
Invoke-RestMethod http://127.0.0.1:9000/v1/models?health=1
Invoke-RestMethod http://127.0.0.1:2337/v1/models
Invoke-RestMethod http://127.0.0.1:9000/api/agent/auth-status
Invoke-RestMethod http://127.0.0.1:8890/v1/agent-fabric/contracts/endpoints
Invoke-RestMethod http://127.0.0.1:8890/v1/agent-fabric/models/local
Invoke-RestMethod http://127.0.0.1:5175/runtime/health
```

## Implementation Rules

1. Keep VRM Sandbox pointed at shim public lane (`9000`) unless operator explicitly overrides.
2. Route behavior changes behind the shim contract (connector/policy/adapter), not by changing operator-facing endpoints.
3. Keep model authority shim-first:
   - manual loading is owned by shim/control center
   - consumer apps read routed state; they do not self-select alternate brains
4. Verify post-change behavior with real calls, not UI-only assumptions.
5. Do not let LM Studio `:1234` or other legacy direct ports become the authority source in docs, scripts, or validation examples.

## Required Evidence

- pre-change and post-change endpoint status with status codes
- exact files changed for shim, PC Control, and VRM Sandbox
- one successful routed chat request proving one-brain behavior
- explicit note if any lane remains degraded

## Scope Boundary

Use this skill for cross-repo routing alignment among:

- the shim repo
- the PC Control repo
- the avatar runtime repo

If the request expands beyond these lanes, route through `$skill-hub`.

## Reference

- `references/routing-contract.md`

## Loopback

If evidence is incomplete or contradictory:

1. stop implementation edits
2. rerun sub-agent + PC Control evidence pass
3. resume only after the `9000` public-lane contract is re-confirmed
