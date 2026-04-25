# Media Image Batch Checklist

## Recovery Pass

- load the latest quest, resume, or workstream artifact before generating anything new
- if the lane is broken or ambiguous, build a deterministic recovery packet (see `recovery-workflow.md`) and attach it to the recovery note
- reopen the active hot-batch folder and confirm the accepted keepers already on disk
- review the direct identity roots before any AI-derived or style-adjacent sources
- review the accepted native keepers and any refined or upscaled anchors currently driving continuity
- review cyberpunk, Starfield, maid, wardrobe, or location source roots separately so style context does not overwrite identity
- confirm both the raw native output folder and the deterministic local review destination
- capture the resumed next step before you generate the next still

## Reference Pass

- choose the best local identity anchors
- include prior accepted native keepers when they improve continuity
- include scene or wardrobe references only if they materially improve the shot

## Native Generation Pass

- keep the requested batch count explicit
- capture the prompt family
- preserve the raw native output paths
- treat the raw native stills as the source-of-truth fallback until a refined keeper proves itself

## Review Pass

- show the results locally before workbench intake
- gather operator feedback
- review the batch yourself with concrete identity and wardrobe notes
- run the strongest available local vision lane on the current batch
- fail closed if the review evidence is incomplete
- turn both review passes into explicit edit guidance before refining

## Local Refinement Pass

- refine or regenerate the strongest candidates from the review notes
- use a local photo-edit refine pass when the still is strong but needs cleanup before upscale
- reject refined derivatives that do not outperform the raw native still on review
- only after refinement passes should a local upscale run
- default to `RealESRGAN x2` for batched keepers unless `x4` is explicitly requested
- keep the refined and upscaled copies next to the native original or in the dedicated review folder
- record the refined keeper path plus the upscale engine and scale factor
- record an accept or reject decision for each reviewed keeper

## Handoff Pass

- still approved
- review completed
- refinement path recorded
- upscale path recorded
- only then stage into Media Workbench or any later clip/video lane
