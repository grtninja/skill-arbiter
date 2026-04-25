---
name: "voice-catalog-runtime-alignment"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Align documented voice-command catalogs, endpoint action allowances, and live runtime handlers so operator-visible voice surfaces match what the stack can actually execute. Use when voice command docs, parser matrices, endpoint permissions, or runtime action routing drift apart."
---

# Voice Catalog Runtime Alignment

Use this skill when the documented voice-command surface and the live runtime behavior need to be reconciled as one contract.

## Workflow

1. Identify the operator-visible voice catalog:
   - command matrices
   - dashboard/help surfaces
   - endpoint admission or permission docs
2. Inspect the runtime owners that actually execute voice actions:
   - parser and routing handlers
   - endpoint admission rules
   - backend action bridges
3. Compare catalog entries against live runtime support:
   - implemented and allowed
   - implemented but undocumented
   - documented but missing
   - blocked by policy on purpose
4. Repair the smallest authoritative layer first, then update the exposed catalog/help surface.
5. Re-run a bounded voice-path proof and record any remaining blocked or degraded commands explicitly.

## Required Evidence

- visible voice catalog or command matrix checked
- runtime handler or permission surface checked
- explicit mismatch list or confirmation of parity
- bounded validation note for at least one live voice or command-path proof

## Guardrails

- Do not expose commands in docs or UI that the active runtime cannot safely honor.
- Keep source-aware filtering and endpoint permissions explicit.
- Do not bypass backend policy just to make catalog and runtime appear aligned.
- Fail closed if command ownership is ambiguous across parser, endpoint, and backend layers.

## Best-Fit Companion Skills

- `$distributed-voice-plane-governance`
- `$shockwave-voice-command-governance`
- `$endpoint-admission-voice-actions`
- `$catalog-snapshot-consistency`

## Scope Boundary

Use this skill only for catalog-versus-runtime alignment in voice-command systems.

For pure parser implementation work or speech-plane transport issues, route through the more specific voice/runtime skill and return here to reconcile the visible catalog afterward.
