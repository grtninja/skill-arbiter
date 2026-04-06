---
name: endpoint-admission-voice-actions
description: Admit Penny voice endpoints with explicit identity, role, and action limits before they can issue backend actions. Use when edge voice devices, endpoint profiles, or voice-initiated tool permissions change.
---

# Endpoint Admission Voice Actions

Use this skill for the endpoint-admission and voice-action-governance lane in the distributed Penny stack.

## Workflow

1. Identify the endpoint class, owner, and intended role.
2. Verify the minimum admitted metadata before allowing voice actions.
3. Bind allowed tool families and confirmation rules to the endpoint profile.
4. Check for drifted identities, duplicated endpoints, or stale admission state.
5. Keep local audit records for endpoint-issued actions.

## Required Evidence

- endpoint identity and role metadata
- allowed tool families or action limits
- confirmation policy for higher-risk actions
- drift or duplication check result

## Guardrails

- Unknown endpoints fail closed.
- Voice input is not blanket tool authority.
- Admission state must be explicit and reviewable.
- Do not let endpoint convenience bypass local policy.

## Best-Fit Companion Skills

- `$distributed-voice-plane-governance`
- `$skill-enforcer`
- `$local-compute-usage`
- `$docs-alignment-lock`

## Scope Boundary

Use this skill only for endpoint admission and voice-action permissioning.

For speech-loop transport behavior itself, route through `$distributed-voice-plane-governance`.
