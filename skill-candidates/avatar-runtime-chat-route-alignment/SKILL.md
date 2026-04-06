---
name: avatar-runtime-chat-route-alignment
description: Align desktop autonomy, speech fallback, live research, and chat-route runtime behavior across avatar-facing local apps after model-plane or harness shifts. Use when runtime handoff and UI behavior change together.
---

# Avatar Runtime Chat-Route Alignment

Use this skill when avatar-facing desktop apps drift across autonomy, chat routing, speech fallback, and live runtime handoff behavior.

## Trigger Conditions

Use this skill when recent changes touch a mix of:

- desktop entry/runtime files
- chat route runtime or bridge logic
- browser or local speech fallback
- live research or autonomy loops
- avatar-pane or control-rail UI surfaces tied to runtime state

Route elsewhere when:

- the task is purely a material/rendering problem: use the most specific VRM rendering skill
- the task is only about public model-lane authority: use `$shim-pc-control-brain-routing`
- the task is only about UI styling without runtime behavior changes: use the relevant frontend skill

## Workflow

1. Capture the intended runtime handoff:
   - who owns chat-route state
   - how speech fallback is selected
   - where autonomy/live research loops feed the UI
2. Inspect the desktop entrypoint and runtime bridge files before editing.
3. Confirm local model-plane assumptions and endpoint ownership.
4. Patch route selection, runtime fallback, and UI state handling together.
5. Validate with a real runtime pass:
   - desktop starts
   - chat route resolves correctly
   - speech fallback behavior is explicit
   - autonomy/research loop state is surfaced in the UI
6. Record any remaining degraded runtime lanes or manual fallback paths.

## Required Evidence

- runtime entry files touched
- route/fallback files touched
- UI surfaces tied to runtime state
- validation notes from an actual app run or smoke test

## Guardrails

- Do not treat UI-only rendering as proof that runtime routing is correct.
- Keep fallback choice explicit; avoid silent provider swaps.
- Prefer one clear runtime owner for chat-route state.
- Fail closed when autonomy/live research changes are not reflected in the operator-visible UI.

## Scope Boundary

Use this skill for avatar-app runtime alignment across chat routing, autonomy, speech fallback, and desktop handoff.

Do not use it for packaging-only changes, Blender/asset work, or repo-agnostic UI styling.

## References

- `$heterogeneous-stack-validation`
- `$shim-pc-control-brain-routing`
- `$desktop-startup-acceptance`
