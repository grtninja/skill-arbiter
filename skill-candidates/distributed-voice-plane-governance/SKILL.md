---
name: "distributed-voice-plane-governance"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Govern the local-first Penny speech plane across ASR, TTS, endpoint voice behavior, and backend action routing. Use when Shockwave, AvatarCore, VRM Sandbox, or control-plane voice contracts shift together."
---

# Distributed Voice Plane Governance

Use this skill when the Penny voice fabric changes across multiple local repos.

## Workflow

1. Confirm the canonical speech-plane owners for ASR, TTS, and endpoint control.
2. Inspect local loopback contracts before touching higher-level orchestration.
3. Keep voice capture, transcript routing, backend action governance, and playback ownership aligned.
4. Validate the speech loop with a bounded readiness or smoke sequence.
5. Record any degraded or fallback voice paths explicitly.

## Required Evidence

- ASR and TTS owner surfaces involved
- endpoint or backend routing rule touched
- bounded speech-loop validation note
- any fallback or degraded path still present

## Guardrails

- Do not let endpoints bypass backend policy.
- Keep the speech plane local-first.
- Do not introduce direct cloud dependence as the canonical voice path.
- Fail closed if voice routing drifts from the documented owner ports or services.

## Best-Fit Companion Skills

- `$voice-call`
- `$local-compute-usage`
- `$heterogeneous-stack-validation`
- `$skill-enforcer`

## Scope Boundary

Use this skill only for cross-repo speech-plane contracts and governance.

For one repo's TTS or ASR implementation details, route to the repo-specific voice or runtime skill.
