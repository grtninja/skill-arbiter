---
name: "vroid-template-asset-sync"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Discover and normalize VRoid/AvatarMaker clothing templates and texture assets into a deterministic manifest for Blender and Unity lanes. Use when template paths are inconsistent or assets were saved manually."
---

# VRoid Template Asset Sync

Use this skill to stop guessing where templates/assets live before avatar build work.

## Workflow

1. Scan known local VRoid/AvatarMaker roots.
2. Detect dress/shoe/body templates and associated textures.
3. Build a normalized manifest JSON with absolute paths and hashes.
4. Copy selected assets into a stable workspace mirror if requested.
5. Emit missing-file warnings for incomplete template sets.

## Scope Boundary

This skill only covers clothing/template asset normalization.

For VRoid Studio Photo Booth animation extraction and `.vrma` conversion, route
to `vroid-vrma-photobooth-pipeline`.

## Commands

Scan and emit manifest:

```bash
python3 scripts/scan_templates.py \
  --json-out /tmp/vroid-template-manifest.json
```

Scan and mirror to workspace:

```bash
python3 scripts/scan_templates.py \
  --mirror-root /path/to/workspace/assets/templates \
  --json-out /tmp/vroid-template-manifest.json
```

## References

- `references/path-priority.md`
- `references/template-contract.md`

## Loopback

If required template classes are missing (body/dress/shoes):

1. Mark manifest as incomplete.
2. Stop build lane.
3. Resume only after missing classes are present.
