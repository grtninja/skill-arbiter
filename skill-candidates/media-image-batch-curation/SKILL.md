---
name: "media-image-batch-curation"
description: "Generate, dual-review, refine, and upscale deliberate still-image batches through the requested still-image engine plus local refinement in <PUBLIC_MEDIA_SCOPE>. Use when reference libraries, batch count, local preview, agent review, local vision review, RealESRGAN x2 or x4 refinement, and Media Workbench intake must stay in one deterministic still-image workflow."
metadata:
  author: "grtninja"
  canonical_source: "https://github.com/grtninja/skill-arbiter"
---

# Media Image Batch Curation

Use this skill for the still-image lane that happens before Media Workbench ingestion or any deliberate video-mode switch.

Use the same QA philosophy as the video lane: preserve the raw native source of truth, gate progression on explicit review, reject refined derivatives that do not beat the native candidate, and only upscale accepted refined stills.

Do not route routine one-off Codex image requests here by default. Keep normal built-in Codex image turns on the native image path unless the operator explicitly asks for batch curation, local review, or workbench handoff.

## Workflow

1. If the still lane is resumed after a disconnect, thread break, or compaction, run the recovery workflow first.
2. Curate the strongest local reference images first.
3. Keep still-image generation in the current mode; do not switch to video mode for stills.
4. Generate the first native batch through the currently requested still-image engine with an explicit batch count.
5. Save the raw native outputs into a deterministic local review folder.
6. Present the results locally before any workbench intake.
7. Run a dual review pass: Codex review plus the strongest available local vision lane.
8. Fail closed if either review surface is unavailable instead of silently advancing the batch.
9. Turn the review notes into concrete edit guidance and refine or regenerate the strongest candidates.
10. When the raw still is close but not final, prefer a local photo-edit refine pass before upscale.
11. Accept only refined stills that outperform the raw native candidate on review.
12. After the refinement pass succeeds, run a deterministic local upscale on the refined keepers.
13. Default to `RealESRGAN x2` for batched stills; use `x4` when the operator explicitly wants the larger pass or the image needs it.
14. Hand approved stills into Media Workbench only after the dual-review and upscale loop is satisfied.

## Recovery Workflow

When this lane breaks mid-batch, recover from local evidence instead of memory:

1. Load the latest quest, resume, or workstream artifact and capture the recorded next step before generating anything new.
2. Open the active hot-batch folder and confirm which stills are already accepted, which are pending review, and which filenames or numbering slots are still open.
3. Review the strongest direct identity roots first so real-person structure wins over derivative styling.
4. Review the accepted native keepers and any refined or upscaled derivatives that are actively serving as identity anchors.
5. Review style-adjacent context roots separately, such as cyberpunk, Starfield, maid, outfit, or location folders, so mood references inform the branch without overwriting identity.
6. Confirm the raw native output location plus the deterministic local review destination for the next batch.
7. Only after the current source families and hot-batch state are visible should the next prompt family or branch direction be chosen.
8. Record the resumed next step in a workstream, quest artifact, or recovery note before generating the next still.

If you need a deterministic resume artifact (recommended), build the recovery packet using the Media Workbench tool and attach it to the recovery note:

- `references/recovery-workflow.md` includes the runnable command for `<PRIVATE_REPO_ROOT>\tools\build_still_image_recovery_packet.py`

## Identity And QC Invariants

- For Penny identity work, always anchor the face on an approved high-quality closeup before accepting a baseline or variants.
- Use a consistent, high reference count per generation when the active engine supports references; record the exact reference set used.
- For Penny outfit sets, the set contract and approved outfit samples are a hard QC gate. If the outfit family changes, the candidate is not a keeper even when identity, tattoo, anatomy, and lighting pass.
- For cyberpunk, sci-fi, command, lounge, catsuit, halter, and glamour sets that Eddie has marked as too PG, require mature adult-glam wardrobe language such as skin-forward but clothed cutouts, open-back or side panels, high slits, exposed shoulders, thigh-high stockings or boots, body-hugging one-piece suits, and confident magazine-cover energy when the set contract allows it.
- Mark conservative officewear, generic dresses, safe uniforms, or bland catalog-fashion results as `TOO_PG_FOR_SET` / `OUTFIT_CONTEXT_DRIFT` when the target set calls for adult-glam styling.
- If the right upper arm is visible, the Celtic-knot tattoo must also be visible on the right upper arm unless the image is intentionally mirrored and recorded as such.
- If tattoo, face, hands, age, body proportions, outfit length, or asymmetry drift is detected, move the item to defects and do not refine, polish, or upscale it until a corrected rerender passes QC.
- Once a baseline is accepted for a set, map variants as outfit-based keyframes with compatible 9x16 and 16x9 progression for later image-to-video transitions.
- Hosiery is optional unless the outfit set calls for it; absence alone is not a defect unless the prompt or set contract required it.

## Runtime Contract

- authoritative local model plane: `http://127.0.0.1:9000/v1`
- hosted large-model review lane: `http://127.0.0.1:2337/v1`
- PC Control hub: `http://127.0.0.1:8890/v1`
- STARFRAME continuity plane: `http://127.0.0.1:8800/v1`
- native Codex still outputs: `%USERPROFILE%\.codex\generated_images`
- local media library root: `D:\Eddie\Pictures`
- local AMUSE model shelf: `H:\Eddie\AI\Amuse\Models`
- local upscale shelf: `H:\Eddie\AI\Amuse\Models\Upscale-amuse`

## Required Evidence

- recovery artifact or resume artifact consulted when the lane was resumed
- active hot-batch folder and current accepted keepers confirmed when resuming
- reference files chosen
- direct identity sources reviewed before style-adjacent sources
- generation prompt or prompt family captured
- batch count recorded when variants are requested
- local preview or Explorer presentation completed
- Codex review notes captured
- local vision review feedback captured
- refinement decision or rerun notes captured
- acceptance or rejection decision captured for each reviewed keeper
- upscale engine and scale factor captured
- final keeper path after local refinement and upscale

## Guardrails

- Do not resume a broken still lane from memory when a quest file, resume note, hot-batch folder, or accepted keepers are available locally.
- Do not auto-switch into video generation just because a still exists.
- Do not ingest into Media Workbench before local preview and review.
- Do not throw away the native Codex output once a refined local copy exists.
- Do not let identity-heavy work ignore the strongest local references.
- Do not skip the local vision review when the large multimodal lane is available.
- Do not let missing review evidence auto-pass a still; this lane is fail-closed.
- Do not let a refined derivative replace the raw native source of truth without beating it in review.
- Do not skip the local photo-edit refine pass when the review notes point to a salvageable still.
- Do not run the final upscale before the refinement pass has been accepted.
- Do not silently choose an upscale engine; record whether `RealESRGAN x2` or `RealESR General 4x` was used.
- Keep outputs local and deterministic.

## Best-Fit Companion Skills

- `$openai-image-gen`
- `$media-staging-prompthead-ops`
- `$media-workbench-desktop-ops`
- `$local-compute-usage`
- `$skill-quest-propagation`

## References

- `references/workflow-checklist.md`
- `references/recovery-workflow.md`

## Scope Boundary

Use this skill for still-image generation, batching, review, and refinement before workbench/video handoff.

Do not use it for:

1. direct video generation
2. generic Comfy-only queue management without the still-review loop
3. non-image repo work

## Loopback

If the still workflow stalls:

1. run the recovery workflow against the current lane before touching generation again
2. reopen the latest local preview folder
3. re-run the dual review step against the current batch
4. continue only after the next refine, rerun, or upscale step is explicit
