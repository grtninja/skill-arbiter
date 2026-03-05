---
name: vroid-vrma-photobooth-pipeline
description: Extract VRoid Studio Photo Booth animation clips from a local AssetRipper Unity export and batch-convert them into valid .vrma files via Unity + UniVRM. Use when direct AssetBundle loading fails due Unity version/build-target mismatch.
---

# VRoid VRMA Photo Booth Pipeline

Use this skill to convert VRoid Studio Photo Booth motions into real `.vrma` files.

## Workflow

1. Export `data.unity3d` to a Unity project with AssetRipper (local, manual step).
2. Prepare the exported project for UniVRM batch export.
3. Run Unity batch export for `.anim` clips under Photo Booth roots.
4. Verify summary and `VRMC_vrm_animation` presence across all outputs.
5. Open output folder for manual inspection.

## Commands

Prepare AssetRipper-exported project:

```bash
python3 scripts/prepare_unity_project.py \
  --unity-project "C:/path/to/ExportedProject" \
  --univrm-root "C:/path/to/univrm-0.128.0" \
  --json-out .tmp/vroid-vrma-prepare.json
```

Run Unity batch export:

```bash
python3 scripts/export_vrma_batch.py \
  --unity-exe "C:/Program Files/Unity/Hub/Editor/6000.3.5f2/Editor/Unity.exe" \
  --unity-project "C:/path/to/ExportedProject" \
  --out-dir "C:/path/to/vroid_photobooth_vrma_out" \
  --json-out .tmp/vroid-vrma-export.json
```

Verify output integrity:

```bash
python3 scripts/verify_vrma_outputs.py \
  --out-dir "C:/path/to/vroid_photobooth_vrma_out" \
  --json-out .tmp/vroid-vrma-verify.json
```

## References

- `references/workflow.md`
- `references/troubleshooting.md`

## Loopback

If export summary shows failures:

1. Stop and inspect `failed` rows in `vrma_export_summary.tsv`.
2. Re-run with `--limit` + `--name-filter` to isolate clips.
3. Resume full export only after isolated export succeeds.
