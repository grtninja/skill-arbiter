# Complete Work Loop

Use this sequence when the goal is a real, high-quality Penny media pass rather than an isolated render.

## Order

1. Initialize a job folder with `scripts/init_media_job.py`.
2. Lock the source and stage a safe render input.
3. Generate a forward-only native Wan clip.
   - One approved still may be reused as both first and last frame for a living-portrait loop baseline.
   - A range of approved keyframes should run through `scripts/run_keyframe_range_pipeline.py` so each adjacent pair becomes a deterministic Wan FLF segment.
4. Review each completed raw slice immediately with a review sheet and the multi-lane review bundle.
   - Radeon review and MX3 QC should start on `slice_completed`, not after the whole batch is done.
   - If the batch started before the latest event-driven runner patch, attach `tools/monitor_segmented_batch.py --review-completed-slices --watch-until-idle` so review still keeps pace with completed slices.
5. Master to `30` or `60` fps with `RIFE` or `FILM`.
6. Generate or import TTS audio if the clip needs speech.
   - For Penny, use the approved local Kokoro `af_jessica` voice unless the user explicitly chooses another approved voice.
   - Match the approved local speech profile: `lang=en-US`, `speed=0.92`, `pitch=0.0`, `accent=neutral`.
7. Run lip-sync on the approved animated clip, not on a rigid still-image benchmark, unless the user explicitly wants a talking-head test.
   - `scripts/run_musetalk_pass.py` is the current local spoken pass lane.
8. Run local ASR QC with `scripts/analyze_spoken_clip.py`.
9. Hand approved components to CapCut for loop join, captions, and final editorial polish.
10. Keep the manifest, prompt/result JSON, QC outputs, and final export together.

## Non-Negotiables

- Do not destructively crop the source by default.
- Do not confuse a smoke test with a quality result.
- Do not build the reverse loop leg until the forward clip is approved.
- Do not let one oversized slice pin the whole batch. Prefer smaller conservative segments that stay clearly under the measured wall-time budget.
- Do not use Windows fallback voices for Penny quality passes when Kokoro `af_jessica` is available locally.
- Do not call a spoken clip good unless the local ASR pass agrees with the expected line closely enough.
- Do not treat CapCut as the source of truth. The raw forward render and the mastered forward clip must remain intact.

## Native / Mastering Split

- Wan raw render: native `16 fps`
- Lip-sync prep: normalize talking clips to `25 fps`
- High-fps delivery: `30` or `60` after raw approval using VFI

## Quality Gates

- Visual gate: Penny still reads as Penny.
- Motion gate: the raw clip is worth mastering.
- Speech gate: transcript fidelity passes.
- Editorial gate: the loop join or spoken cut feels intentional rather than stitched together.
