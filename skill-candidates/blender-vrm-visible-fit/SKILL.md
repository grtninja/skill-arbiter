---
name: blender-vrm-visible-fit
description: Run a checkpointed, in-foreground Blender workflow for VRM clothing fit and rig transfer. Use when dress/shoe fitting must be reviewed live before export and destructive body edits are not acceptable.
---

# Blender VRM Visible Fit

Use this skill for manual-in-the-loop Blender avatar fitting where the user must see each change before export.

## Workflow

1. Open Blender in foreground with exactly one clean scene file.
2. Import base VRM and verify full body continuity before any edits.
3. Import clothing asset VRM/mesh and isolate only required materials (dress, shoes).
4. Align clothing in viewport with user-visible checkpoints.
5. Transfer/bind weights with robust transfer tools.
6. Run pose stress checks (hips, knees, elbows, shoulders, ankles).
7. Export Blender-pass VRM only after user approval.
8. Record build evidence JSON and screenshots.

## Hard Rules

- Never run hidden background rebuilds for fit-critical edits.
- Never delete base body geometry before user fit approval.
- Never use global hole-fill on body meshes.
- Keep shoes as an independent mesh lane unless the source requires merge.

## Commands

Checkpoint snapshot:

```bash
python3 scripts/checkpoint_state.py \
  --scene /path/to/scene.blend \
  --stage "after_weight_transfer" \
  --json-out /tmp/blender-vrm-checkpoint.json
```

## References

- `references/visible-fit-checklist.md`
- `references/open-source-tooling.md`

## Loopback

If fit/rig quality is uncertain:

1. Stop export.
2. Capture current checkpoint JSON + screenshots.
3. Return to stage `align` or `weight_transfer` and continue visibly.
