# Media Mode Checklist

## Before Render

- Confirm the source library stays read-only.
- Stage source images into a workspace or Comfy input folder.
- Build a contact sheet if multiple recent candidates exist.
- Choose a source with usable composition.
- Confirm whether the run is `smoke_test` or `quality_render`.

## GPU Mode

- If a heavy chat model is resident on NVIDIA VRAM, unload it first when the media run needs that headroom.
- If alternate chat capacity exists on another GPU or host, defer chat there during the render.
- Keep both NVIDIA devices visible when using MultiGPU nodes.

## Render

- Inspect node/object schema or template limits before selecting clip length.
- Use the longest practical clip length for `quality_render`.
- Save prompt and result JSON next to the output.

## After Render

- Open the output folder in Explorer.
- Close stray Comfy/Python consoles if the run is complete.
- If quality is poor, classify the failure before rerunning:
  - bad source
  - bad composition staging
  - bad prompt
  - bad device placement
  - model/runtime limitation
