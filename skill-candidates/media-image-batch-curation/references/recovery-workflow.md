# Still Image Recovery Workflow

Use this recovery pass whenever a native still-image lane is interrupted by a broken thread, compaction, reconnect failure, or session restart.

## Build A Deterministic Recovery Packet (Executable)

When the still-image lane is broken and you need a deterministic resume point, build a recovery packet from local artifacts (task + resume) plus the active hot-batch folder.

Run from PowerShell:

```powershell
python '<PRIVATE_REPO_ROOT>\tools\build_still_image_recovery_packet.py' `
  --task-json 'D:\path\to\still_task.json' `
  --resume-json 'D:\path\to\still_resume.json' `
  --hot-batch-dir 'D:\Eddie\Pictures\...\hot-batch' `
  --out-json 'D:\path\to\recovery\still_image_recovery_packet.json' `
  --out-md 'D:\path\to\recovery\still_image_recovery_packet.md'
```

Required inputs:

- `--task-json`: the current still-image lane task artifact (the packet that lists accepted keepers, previous outputs, or staged candidates).
- `--resume-json`: the lane resume artifact that records `lane`, `next_step`, and `action` for the still-image workflow.
- `--hot-batch-dir`: the active hot-batch folder you are resuming (the folder containing the in-flight stills and keeper numbering).

Expected outputs:

- `--out-json`: the canonical recovery packet with:
  - inferred `next_slot` for `hot-batch-##`
  - `accepted_keepers` extracted from the task artifact
  - `direct_identity_sources` and `style_context_sources` sampled from Media Workbench `media_study.local.json` families
  - `native_output_root` (defaults to `C:\Users\<you>\.codex\generated_images` unless overridden)
- `--out-md` (optional but recommended): a human-readable companion view for quick operator scanning.

Evidence expectations (fail closed if missing):

- the command invocation (or transcript) showing the exact paths used
- the tool stdout line `still_image_recovery_packet=<absolute path>` captured
- the produced `still_image_recovery_packet.json` saved and reviewed (hot-batch `next_slot`, accepted keeper list, and next step all make sense)
- the produced `.md` reviewed by the operator when present

Optional inputs (use when you need to override defaults):

- `--media-study-config`: path to the Media Workbench media study config (defaults to `<PRIVATE_REPO_ROOT>\config\media_study.local.json`).
- `--native-output-root`: the root used for native Codex outputs if you need to override (defaults to `C:\Users\<you>\.codex\generated_images`).
- `--direct-family`: one or more Media Workbench `source_families` ids to treat as direct identity roots (defaults to `real_penny_photo`).
- `--style-family`: one or more `source_families` ids to treat as style context roots (defaults include `cyberpunk_penny_adjacent` and `game_female_character_adjacent`).
- `--style-token`: optional substring filters to narrow style sampling (repeatable).
- `--sample-limit`: how many sample images to include per root/token match (defaults to `8`).

## Recovery Order

1. Load the latest quest, resume, or workstream artifact first.
2. Reopen the active hot-batch folder and verify the current accepted keepers.
3. Review direct identity roots before any derivative or style-adjacent sources.
4. Review the accepted native keepers and the refined or upscaled derivatives that are currently acting as anchors.
5. Review the active style context roots separately:
   cyberpunk, Starfield, maid, wardrobe, location, or mood folders should guide variation, not redefine identity.
6. Confirm the raw native output folder and the deterministic review destination for the next batch.
7. Write down the resumed next step before generating anything new.

## Minimum Recovery Evidence

- quest or resume artifact path
- hot-batch folder path
- accepted keeper paths
- direct identity source roots reviewed
- style-adjacent source roots reviewed
- next filename or batch slot to fill
- next prompt family or branch direction

## Fail-Closed Rules

- Do not resume from chat memory alone when local evidence exists.
- Do not let derivative AI outputs outrank direct Penny photo roots during recovery.
- Do not generate a new batch until the current hot-batch folder state is visible.
- Do not hand a recovered still lane into Media Workbench until review and refinement gates are satisfied again.
