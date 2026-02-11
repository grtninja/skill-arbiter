# Pipeline Contract

## Required Profiles

At least these pipeline profiles should be present when media workflow routing is enabled:

- `small_video_capcut`
- `quality_video_capcut`

## CapCut Export Metadata

When `capcut_preset=true`, pipeline responses should include `capcut_export` with:

- `editor=capcut`
- export transport hints (`container`, `codec`, `fps`)
- one or more operator notes for timeline/export handling

## AMUSE Stage

When `amuse_enhance=true` and AMUSE is enabled, pipeline responses should include additive `amuse` payload with endpoint and status details.

## Failure Modes

Fail closed when:

1. MCP status is not enabled/running.
2. Required Comfy tools/resources are missing.
3. Required pipeline profiles are missing.
4. `capcut_export` contract is absent when `capcut_preset=true`.
5. AMUSE status is unreachable in lanes that require AMUSE.
