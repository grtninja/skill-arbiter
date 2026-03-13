---
name: vrm-material-lighting-debug
description: Diagnose and fix a desktop VRM app's avatar lighting and MToon material failures when a VRM looks washed out, has bright edges, shows inverted-looking cloth shadows, or shades clothing differently from skin and legs. Use when you need to inspect the live .vrm, separate scene-light problems from material problems, patch the correct layer, and verify with a rebuilt packaged app.
---

# VRM Material Lighting Debug

Use this skill for private desktop VRM rendering bugs where the avatar looks overlit, cloth materials glow on the dark side, dress shading disagrees with skin or legs, or scene-light tweaks are not fixing the real problem.

## Workflow

1. Split the problem before editing code.
   - If the whole avatar is washed out, inspect scene lighting first.
   - If skin or legs shade correctly but dress or cloth does not, inspect live VRM materials first.
   - If one mesh still looks wrong after material fixes, inspect normals last.
2. Inspect the active `.vrm` instead of guessing from screenshots alone.
   - Run `scripts/inspect_vrm_materials.py` on the live avatar under the app's roaming avatar store.
   - Compare one correctly shaded material against the broken cloth material.
3. Patch the correct layer in `<PRIVATE_REPO_D>/packages/engine/src/index.ts`.
   - Scene-light issue: reduce fill and rim before touching materials.
   - Cloth-only issue: patch `applyMtoonCompatibilityFixes`.
   - Bright "shadow" side: derive cloth `shadeColorFactor` from the base color and darken it hard.
4. Rebuild and relaunch cleanly.
   - Stop the running app.
   - Repack with `npm --workspace <PRIVATE_PACKAGE_SCOPE>/desktop run pack`.
   - Relaunch the packaged app with `explorer.exe`, not `cmd /c start`.
5. Verify with both health and viewport checks.
   - Confirm `http://127.0.0.1:5175/health` is green.
   - Confirm dress or cloth dark sides actually read dark and bright rims are gone.

## Commands

Inspect live VRM materials:

```bash
python scripts/inspect_vrm_materials.py \
  --vrm "$env:USERPROFILE/AppData/Roaming/<PRIVATE_PACKAGE_SCOPE>/avatars/<avatar-id>/<avatar>.vrm" \
  --name-filter "cloth|dress|onepiece|bottoms|skin|body|leg" \
  --json-out .tmp/vrm-materials.json
```

Rebuild and relaunch the packaged desktop app cleanly:

```bash
Get-Process "<PRIVATE_DESKTOP_APP>" -ErrorAction SilentlyContinue | Stop-Process -Force
npm --workspace <PRIVATE_PACKAGE_SCOPE>/desktop run pack
Start-Process explorer.exe "$env:USERPROFILE\\Documents\\GitHub\\<PRIVATE_REPO_D>\\apps\\desktop\\release\\win-unpacked\\<PRIVATE_DESKTOP_APP>.exe"
```

## What To Inspect

Read `references/material-triage.md` when the problem is not obviously global lighting.

Focus on these material fields first:

- `doubleSided`
- `shadeColorFactor`
- `giEqualizationFactor`
- `matcapFactor`
- `rimLightingMixFactor`
- `parametricRimLiftFactor`
- `shadingToonyFactor`
- `shadingShiftFactor`

Use `references/vrm-sandbox-engine-hotspots.md` when you need the code locations that normally own the fix.

## Hard Rules

- Do not keep lowering global light levels once the problem is isolated to cloth materials.
- Do not leave cloth `shadeColorFactor` near white when the dress base color is dark red.
- Do not use `cmd /c start` to relaunch the desktop VRM app on Windows.
- Do not claim the issue is fixed until the packaged app is rebuilt and the live viewport matches the intended dark-side shading.

## Loopback

If the dress or cloth still shows a bright dark-side band after the first material pass:

1. Re-run the live VRM inspector and confirm the actual cloth material names.
2. Compare the bad cloth material against a correctly shaded leg or skin material.
3. Tighten only the affected cloth materials by name.
4. If cloth shading is sane but one mesh still looks wrong, inspect that mesh's normals next.
