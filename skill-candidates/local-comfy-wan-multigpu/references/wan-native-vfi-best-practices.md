## Wan Native + VFI Best Practices

This note records the current evidence-backed defaults for local Wan image-to-video work.

### Source-Backed Defaults

Official/current source points:

- Wan 2.1's public README examples export at `fps=16`, and its image-to-video guidance centers on `480P (~81 x 480 x 832)` sized runs while preserving the source image aspect ratio.
- Comfy's official `image_to_video_wan` template uses `512x512`, `33` frames, and `CreateVideo` at `16` fps.
- Comfy's official `video_wan2_2_14B_i2v` template subgraph uses `640x640`, `81` frames, `CreateVideo` at `16` fps, `4` Euler/simple steps, SD3 shift `5`, and the Wan 2.2 Lightx2v 4-step LoRAs.
- The `ComfyUI-Frame-Interpolation` node pack exposes `RIFE VFI`, `FILM VFI`, `GMFSS Fortuna VFI`, and related tools inside Comfy.
- The RIFE project explicitly calls out `4.22.lite` as suitable for post-processing some diffusion-model videos, and its inference tool supports exact fps targets such as `--fps=60`.

### Practical Conclusion

The better local workflow is:

1. render Wan at native cadence
2. approve the motion and continuity
3. if speech is needed, synthesize the line with the approved local voice lane before lip-sync review
4. interpolate the approved forward clip upward to `30` or `60` fps with a dedicated VFI model
5. if looping is needed, create the reverse leg after approval and assemble it editor-side
6. upscale after interpolation

Do not force Wan itself into a fake low-fps or arbitrary high-fps lane when the model family and official templates are built around `16` fps output.

### Recommended Profiles

#### Dry Run

Use this when validating the shot, not finishing it.

- native `16` fps
- `81` frames as the default useful dry run
- `480p`-class area or portrait-equivalent area
- `4` steps with the official Lightx2v LoRAs
- subtle motion only

Portrait-equivalent dry-run targets that preserve Penny better than the earlier undersized test:

- `480x848`
- `512x912`

Avoid sub-`16` fps dry runs unless there is a very specific reason.

#### Quality Render

Use this only after the dry run already looks like Penny.

- native `16` fps raw render
- `121` to `161` frames when the machine stays stable
- portrait-equivalent `640`-class or `720`-class dimensions if VRAM allows
- keep motion simple and loop-friendly

#### High-FPS Master

Use a VFI pass after raw approval:

- `RIFE VFI` for general diffusion-video post
- `FILM VFI` if the source motion is sparse or the loop source is extremely short
- exact output targets: `30` or `60` fps

#### Loop-Focused Render

If the final deliverable should loop, prefer a loop-aware Wan path instead of depending only on a ping-pong master.

Local runtime discovery on this machine shows:

- `WanFirstLastFrameToVideo`
- `WanAnimateToVideo`

Those should be preferred over a plain one-way `WanImageToVideo` render when loop closure matters.

If a manual/editorial loop is acceptable, the better finishing order is:

1. render and approve the full forward clip
2. if speech is needed, lip-sync the approved forward clip instead of a rigid still benchmark
3. create the reverse leg after approval
4. assemble forward + reverse in CapCut

That is an inference from the current local results: it keeps the raw generation lane honest and makes loop surgery an editorial decision instead of hiding it inside the generation stage.

### Penny-Specific Guardrails

- keep the native Wan run focused on micro-motion, not dramatic action
- preserve full face and upper-body framing
- do not crop down to mouth/chin areas
- do not evaluate loop quality without a review sheet

### Links

- Comfy workflow templates: https://github.com/Comfy-Org/workflow_templates
- Comfy template docs: https://docs.comfy.org/interface/features/template
- Wan 2.1 official repo: https://github.com/Wan-Video/Wan2.1
- ComfyUI Frame Interpolation: https://github.com/Fannovel16/ComfyUI-Frame-Interpolation
- RIFE official repo: https://github.com/hzwer/ECCV2022-RIFE
