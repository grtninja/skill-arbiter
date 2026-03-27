# Penny Edge Governance

This reference describes how skill-arbiter should govern the distributed Penny voice fabric.

## Purpose

Distributed Penny endpoints should never become a loophole that bypasses local governance. The voice fabric still needs:

- tool gating
- endpoint admission
- policy-aware action limits
- clear local-first safety behavior

## Governance rules

- endpoint voice input is not equivalent to unrestricted tool authority
- edge devices may request actions, but backend policy decides execution
- only admitted devices should reach the Penny edge ingress
- direct backend model surfaces should remain non-endpoint-facing by default

## Recommended arbiter roles

### Endpoint admission

- validate endpoint identity
- validate role/profile assignment
- attach trust status to the endpoint record

### Runtime action governance

- enforce allowed tool families for voice-initiated actions
- require confirmation on higher-risk operations
- preserve local audit records for endpoint-issued actions

### Drift detection

- detect endpoint routing that bypasses the normal local cognition path
- detect policy mismatches between endpoint class and allowed tool surface
- detect duplicated or stale endpoint identities

## Cross-repo tie-ins

- private cognition/persona repo: continuity and operator identity
- private speech-loop repo: voice contract and routing alignment
- private distributed-node repo: node registry and coordination
- private desktop-control repo: rollout and startup ownership

## Immediate next work

1. Add a personal-policy profile for Penny voice endpoints.
2. Define the minimum admitted metadata required before an endpoint can issue voice actions.
3. Add a fail-closed rule for unknown or drifted endpoint identities.
