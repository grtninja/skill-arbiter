---
name: skill-openclaw-nullclaw-integration
description: Reconcile OpenClaw and NullClaw upstream changes into router-aware MeshGPT, MX3 shim, and AvatarCore lanes with privacy-safe attribution, release-provenance gating, and deterministic test gates.
---

# Skill OpenClaw NullClaw Integration

Use this skill for cross-repo integration work when OpenClaw/NullClaw changes need to land in local router/model/API routing behavior.

## Workflow

1. Pull third-party sources fast-forward only.
2. Build a bounded change inventory focused on routing, providers, channels, agent orchestration surfaces, and security advisories.
3. Verify release provenance state before trusting an upstream version bump:
   - patched/advisory version line
   - whether signed tags or artifact digests are actually verifiable
   - whether local policy should block auto-apply pending provenance
4. Map findings into local repository lanes:
   - Repo A coordinator/runtime routing
   - Repo B AvatarCore routing profiles
   - MX3 shim model-router policy
   - control-plane release gating / fail-closed policy
5. Apply deterministic patches and run lane-specific tests.
6. Refresh third-party attribution and intake evidence.
7. Run `skill-auditor` + `skill-arbiter-lockdown-admission` before completion.

## Canonical Commands

```bash
git -C <THIRD_PARTY_CLONES>/openclaw pull --ff-only
git -C <THIRD_PARTY_CLONES>/nullclaw pull --ff-only
python skill-candidates/skills-third-party-intake/scripts/third_party_skill_intake.py \
  --source-root openclaw=<THIRD_PARTY_CLONES>/openclaw/skills \
  --source-root openclaw-ext=<THIRD_PARTY_CLONES>/openclaw/extensions \
  --source-root nullclaw=<THIRD_PARTY_CLONES>/nullclaw \
  --json-out .tmp/third-party-intake-openclaw-nullclaw.json
```

Focused integration scan:

```bash
rg -n "router|routing|provider|channel|meshrelay|gateway|agent" <THIRD_PARTY_CLONES>/openclaw <THIRD_PARTY_CLONES>/nullclaw
```

## Guardrails

- Never copy secrets, tokens, local usernames, or absolute personal paths from third-party docs.
- Keep imported instructions public-shape only and placeholder-safe.
- Prefer upgrading existing local skills before adding new overlapping candidates.
- Keep third-party source attribution current in `references/third-party-skill-attribution.md`.
- Do not auto-promote an upstream OpenClaw release on version number alone when provenance or digest verification is missing.

## Scope Boundary

Use this skill only for OpenClaw/NullClaw cross-repo integration and curation.

Do not use it as a general coding workflow skill; route unrelated implementation lanes through `$skill-hub`.

## Reference

- `references/openclaw-nullclaw-integration-map.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the unresolved source delta and impacted local repo lane.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
