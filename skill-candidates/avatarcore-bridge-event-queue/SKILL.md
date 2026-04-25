---
name: "avatarcore-bridge-event-queue"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Operate AvatarCore bridge sessions, heartbeats, engine-event queues, and directive drains as one contract. Use when Unreal bridge lifecycle and queue semantics change together."
---

# AvatarCore Bridge Event Queue

Use this skill when AvatarCore's Unreal bridge session and queue behavior are the main surface.

## Workflow

1. Inspect session create, heartbeat, close, and snapshot behavior together.
2. Check engine-event enqueue and AvatarCore-directive enqueue behavior as paired queues.
3. Verify drain semantics, batch limits, and missing-session failure behavior.
4. Keep bridge state legible for operators and downstream runtime code.
5. Re-run a bounded session and drain proof before closing.

## Required Evidence

- bridge route or session surface touched
- queue or drain behavior touched
- missing-session or close behavior checked
- bounded session proof after the change

## Guardrails

- Do not treat one direction of the bridge as the whole contract.
- Preserve explicit not-found and close behavior.
- Keep queue drains bounded and inspectable.
- Fail closed if heartbeat and queue state diverge.

## Best-Fit Companion Skills

- `$repo-b-avatarcore-ops`
- `$local-trace-evidence-correlation`
- `$distributed-voice-plane-governance`
- `$skill-common-sense-engineering`

## Scope Boundary

Use this skill only for AvatarCore bridge session and event-queue behavior.

For general AvatarCore provider or embodiment work, route through `$repo-b-avatarcore-ops`.
