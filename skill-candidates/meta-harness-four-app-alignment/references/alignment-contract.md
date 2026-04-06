# Four-App Alignment Contract

Use this reference when the four core local app surfaces must be aligned together.

## Authority Rules

- `G:\GitHub` is the canonical active repo root.
- `http://127.0.0.1:9000/v1` is the public authoritative model plane.
- `http://127.0.0.1:2337/v1` is the hosted large-model authoritative lane.
- `http://127.0.0.1:1234/v1` and the LM Studio loaded-models panel are non-authoritative operator surfaces only.

## Surface Order

Repair and validate in this order:

1. PC Control governance surface
2. shim/control-center surface
3. STARFRAME app continuity/defaults
4. avatar runtime defaults and health

## Minimum Validation Set

- governance/status evidence collected first
- `GET /v1/models` or equivalent model-lane checks on `9000` and `2337`
- runtime-health check for the avatar surface when it should be live
- repo-local docs or scope tracker updates where behavior changed
- explicit degraded-lane note for any unfinished slice

## Common Failure Patterns

- path drift back to legacy `Documents\GitHub` aliases instead of canonical `G:\GitHub`
- `:1234` treated as authority instead of a non-authoritative operator surface
- STARFRAME app defaults patched without shim or PC Control truth
- avatar runtime marked healthy from UI state instead of explicit health evidence
- cross-repo doc updates landing only in one control repo
