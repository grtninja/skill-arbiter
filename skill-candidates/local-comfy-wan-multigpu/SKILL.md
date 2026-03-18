---
name: local-comfy-wan-multigpu
description: Operate local-only ComfyUI Wan image-to-video workflows with MultiGPU placement, quality-first source staging, long-clip validation, and Explorer-based export handoff. Use when Codex needs to turn private local stills into local video artifacts without browser-only UX, while avoiding destructive crops, stray console windows, and GPU contention with chat models.
---

# Local Comfy Wan MultiGPU

Use this skill when the goal is a real local media-generation pass, not just an API or health smoke.

All local paths and endpoints in this skill are intentionally parameterized.
Set environment variables (for example `LOCAL_MEDIA_WORKBENCH_TOOLS_ROOT`, `LOCAL_COMFY_*`, and `LOCAL_MUSETALK_REPO`) instead of hardcoding workstation-specific paths.

## Workflow

1. Initialize a deterministic work item folder before heavy generation. Use `scripts/init_media_job.py`.
2. Keep the source library read-only and stage copies into a workspace or Comfy input folder before rendering.
3. Build a thumbnail/contact sheet from candidate stills before choosing a source; do not pick an arbitrary image. Use `scripts/build_contact_sheet.py`.
4. Reject destructive center-crop staging. Preserve composition with fit or pad unless the user explicitly wants a crop.
   - Use `scripts/stage_reference_frame.py` for deterministic fit or pad staging.
5. Distinguish `smoke_test` from `quality_render`:
   - `smoke_test`: shortest cheap proof only.
   - `quality_render`: choose a properly framed source and push the workflow to the longest supported clip length.
   - Inspect the live Wan node schema first with `scripts/inspect_wan_limits.py`.
   - Treat `16 fps` as the native Wan baseline unless a specific workflow proves otherwise.
6. For heavy Wan runs, unload competing NVIDIA-resident chat models first and route chat to another local host/GPU if available.
7. When using MultiGPU nodes, do not hide devices with `--cuda-device`; keep both CUDA devices visible and place loaders deliberately.
8. Start Comfy through a monitored headless launcher that writes logs and fails closed if the server never becomes ready. Use `scripts/launch_comfy_headless.py`.
9. Persist prompt/result artifacts next to the output clip so the exact render path is reproducible.
   - Use `scripts/run_wan_flf2v.py` for first/last-frame quality renders and living-portrait baselines.
   - Use `scripts/run_keyframe_range_pipeline.py` when the user supplies a range of approved keyframes that should become a single complete video.
   - Use `scripts/run_complete_media_loop.py` when the job should drive staging, raw motion, Jessica TTS, MuseTalk, QC, and export packaging in one pass.
10. Extract review frames and build a review sheet from the finished clip with `scripts/review_video_result.py`.
11. Visually inspect the generated review sheet and, when available, capture a local screenshot of the result viewer before deciding the run is acceptable.
12. When the MX3 runtime is available, use it as an assist plane for source scoring and QC rather than as a pretend generator:
   - `face-yunet`, `face-landmarks`, `face-headpose`, `face-eye-state` for source preflight
   - `pose-simcc`, `emotion-ferplus`, `face-eye-state` for raw-render body/eye/expression QC
   - `segmentation-bisenet`, `depth-hr`, and `DaSiamRPN` tracker pair for masks, ROI tracking, and mouth-region inspection
   - `audio-speech-enhancement` only for recorded/noisy audio, not clean Jessica TTS
13. For loop-targeted shots, prefer loop-aware Wan nodes such as `WanFirstLastFrameToVideo` over a plain one-way image-to-video run when they are available locally.
   - Reusing the same approved still as both first and last frame is acceptable for a living-portrait loop baseline.
   - A keyframe range should be treated as ordered endpoints, not as arbitrary cuts to concatenate blindly.
14. When the clip should loop, keep the approved forward render as the source of truth and only build the reverse leg after approval:
   - `scripts/prepare_capcut_loop_handoff.py` for the preferred forward + reverse editor handoff
   - `scripts/run_loop_vfi_master.py` for a Comfy-based VFI master
   - `scripts/make_loop_master.py` only as the fallback ffmpeg-only lane
15. If the user asks for `30` or `60` fps, render Wan at native cadence first and master upward with dedicated VFI instead of pretending Wan itself should be the final `30`/`60` fps source.
16. For longer spoken or directed clips, split the job into phrase-sized raw segments first, then stitch after approval:
   - keep raw Wan slices near a real measured wall-clock budget instead of one giant render
   - current quality-first policy targets about `18` minutes per raw slice with a `30` minute hard cap
   - prefer natural phrase boundaries over arbitrary word chops, and do not split a segment mid-thought just to satisfy a budget
   - for Penny spoken passes, aim for `1` sentence, `6-14` words, and `<= 7s` per accepted spoken slice
   - stitch the approved segment masters after render; do not force a single monolithic raw pass when the workstation can parallelize slices better
   - on current hardware, smaller slices are a feature, not a failure: they improve queue balance, review cadence, retry cost, and whole-system throughput
17. If the clip needs speech, keep TTS/lip-sync as a separate pass and run local ASR QC after it.
   - For Penny spoken passes, use the approved local Kokoro `af_jessica` lane unless the user explicitly chooses another approved voice.
   - Use `scripts/synthesize_kokoro_tts.py` with the local Kokoro model files when the workbench needs a deterministic offline TTS source.
   - Use `scripts/run_musetalk_pass.py` for the current animated-source spoken pass lane.
   - Use `scripts/analyze_spoken_clip.py` to compare the spoken output against the expected line.
   - Treat `LatentSync 1.6` as the primary quality-upgrade target for mouth clarity; treat `MuseTalk` as the current fallback/baseline until the local LatentSync lane is fully installed.
18. Apply lip-sync only after the body or portrait motion pass is approved. A rigid still-image talking head is a benchmark lane, not the final-quality spoken workflow, unless the user explicitly asks for it.
19. Normalize talking-head lip-sync sources to `25 fps` video and `16 kHz` mono audio before MuseTalk / LatentSync-class processing.
20. If the user wants a loop that feels polished rather than algorithmic, finish the forward + reverse assembly in CapCut instead of forcing the whole loop into one automatic render step.
21. Stop at one reviewable finished clip before creating `30/60 fps` variants unless the user explicitly asks for VFI masters.
   - Default spoken/mastered handoff is the reviewed `25 fps` clip.
   - Treat `30/60 fps` as opt-in post-review variants, not the automatic default.
22. Before and after a quality batch, run the heterogeneous workbench evaluation so the pipeline reflects the real machine state:
   - `<WORKBENCH_TOOLS>/evaluate_heterogeneous_media_pipeline.py`
   - treat required local stack services as a prerequisite for media creation; fail closed if those health surfaces are down
   - treat AMUSE on `<AMUSE_BASE_URL>` as a GUI/inventory bridge unless a future native execution API is proven
   - treat `DeviceSelectorMultiGPU` options as the source of truth when `/system_stats` underreports CUDA visibility
   - validate the selected Wan bundle and template currency before heavy rendering with `scripts/validate_wan_bundle.py`
   - fail closed if the selected bundle is incomplete or the template pack is stale for the chosen lane
   - keep the spoken benchmark ladder explicit: `wan22_i2v_a14b_flf2v -> wan22_ti2v_5b -> wan22_s2v_14b -> wan22_animate_14b`
23. Use the workstation heterogeneously instead of forcing every step through one GPU:
   - NVIDIA `5060 Ti`: preferred raw Wan lane and heavier segment owner
   - NVIDIA `4060 Ti`: secondary raw Wan lane with smaller slices matched to its measured throughput
   - Radeon `7600 XT`: peer generation lane when a Radeon Comfy worker is healthy; otherwise use it continuously for AMUSE DirectML generation/repair/upscale, Qwen review, and sidecar critique
   - do not call the Radeon a Comfy peer lane unless a HIP-enabled Comfy runtime is actually live on the configured peer endpoint; OpenCL visibility or AMUSE inventory alone is not enough
   - do not idle the Radeon just because the current raw Wan path is NVIDIA-first; it must always have review, repair, upscale, benchmark, or peer-generation work
24. When MX3 is healthy, switch the shim feeder into media-assist mode before long QC loops:
   - capture feeder status first, then enable media assist, and restore the prior feeder state when the media pipeline exits cleanly
   - `<WORKBENCH_TOOLS>/set_mx3_media_assist_mode.py --mode status`
   - `<WORKBENCH_TOOLS>/set_mx3_media_assist_mode.py --mode enable`
   - `<WORKBENCH_TOOLS>/set_mx3_media_assist_mode.py --mode restore --from <saved-status-json>`
   - run `scripts/mx3_frame_gate.py` on each raw slice before lip-sync; the current implementation is a post-render frame-QC scaffold until a thinner dedicated MX3 face/headpose route is wired
25. Build a structured multi-lane review artifact for every serious batch:
   - `<WORKBENCH_TOOLS>/build_multilane_review_report.py`
   - use Radeon `Qwen3.5-VL` for image review, Radeon `Qwen3.5` text for distillation when useful, and include the current runtime evaluation
   - if an optional local vision supervisor is running, treat its `vision/analyze-frame` surface as an extra review lane
   - when a segmented batch is running, dispatch review immediately on `slice_completed`; do not wait for the whole batch to finish before the Radeon and MX3 start critiquing
   - for already-running batches that started before the latest orchestration patch, attach `<WORKBENCH_TOOLS>/monitor_segmented_batch.py --review-completed-slices --watch-until-idle`
26. Open the export folder in Explorer when finished only when the user actually wants that handoff. Do not treat browser links as the primary handoff.
27. Clean up stray Comfy/Python console windows after the render completes unless the user explicitly wants the console left open.

## Quality Guardrails

- Never reuse a previous cropped poster as the main creative source unless the user asked for that crop.
- Do not present a proof artifact as a quality result.
- If the chosen input is too tight, off-angle, or badly framed, stop using it and stage a better source.
- Prefer face-plus-shoulders, torso, or full-character references over mouth-only or chin-only crops for character animation tests.
- If the render loop loses the Comfy server or the output video record never appears, fail closed and report that explicitly instead of waiting indefinitely.
- Distinguish `raw_render` from `mastered_output`. A higher-fps looping master may be derived from the raw render when that gives a better result than a more expensive rerun.
- Do not call a `6 fps` or similarly under-cranked output a useful dry run unless the user explicitly asked for a bare smoke test.
- Do not let one oversized segment monopolize the slower lane. Re-split before rerendering if the measured slice budget is wrong.
- Do not cut spoken text into nonsense fragments just to satisfy a budget. Prefer phrase-sized splits and only split again when a chunk truly cannot fit the available render lanes.
- Do not accept any slice where Penny turns away from camera or drifts into an off-camera/profile-view pose.
- Do not call a spoken clip acceptable until ASR QC says the spoken line is close enough to the intended line.
- Do not let the lip-sync lane quietly change the intended pacing or phoneme content without recording it in the QC output.
- Do not use Windows SAPI / Microsoft Sam / generic fallback voices for a Penny quality pass when the local Kokoro `af_jessica` lane is available.
- Do not treat a rigid-body talking-head lip-sync pass as the final spoken output when the user wants a full animated result.
- Do not treat MuseTalk output as clean just because ASR passes; inspect the mouth region for flashing, blur, or mask artifacts before accepting it.
- Do not let MX3-side scores override obvious visual failures; MX3 is an assist/QC plane, not final creative judgment.
- Do not create `30/60 fps` variants until the `25 fps` reviewed master is accepted.

## MultiGPU Placement

For Wan image-to-video lanes:

- Use MultiGPU loader variants when available.
- Keep CLIP on CPU when that reduces VRAM pressure without hurting throughput materially.
- Prefer the `5060 Ti` lane for high-noise UNet work and the `4060 Ti` lane for the low-noise / helper lane when both are visible to the runtime.
- Split high-noise and low-noise UNet placement across both NVIDIA GPUs when the workflow supports it.
- Record the actual device placement in the saved prompt artifact.
- For segmented spoken batches with separate single-GPU Comfy lanes, treat throughput benchmarks as planning inputs rather than assuming both cards are equal.

## Long-Clip Rule

When the user asks for a useful render, inspect the live node/object schema or workflow template and choose the longest supported clip length that is practical on the current machine. Do not default to a 4-second or near-minimal clip unless the user asked for a quick smoke.

## Native Cadence Rule

For Wan image-to-video work, prefer the official/native cadence and master upward later:

- raw Wan baseline: `16 fps`
- dry run baseline: `81` frames at a `480p`-class area or portrait-equivalent area
- high-fps master: `RIFE` or `FILM` after raw approval

## Scope Boundary

Use this skill for direct local ComfyUI/Wan media work.

Do not use this skill for:

1. OpenAI Sora/API video generation only.
2. Repo-scoped adapter validation only.
3. Generic video editing guidance without local render execution.

## References

- `references/complete-work-loop.md`
- `references/media-mode-checklist.md`
- `references/mx3-media-assist.md`
- `references/penny-continuity-contract.md`
- `references/review-loop.md`
- `references/source-selection-rules.md`
- `references/wan-native-vfi-best-practices.md`

## Loopback

If the lane is blocked or the render is poor:

1. Capture the exact prompt/result artifact and output path.
2. State whether the failure was source-choice, workflow-choice, model/runtime limits, or shell/UI policy.
3. Re-stage a better source and rerun the longest practical clip instead of defending a bad artifact.
