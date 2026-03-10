# Material Triage

Use this reference when a VRM avatar looks wrong in VRM Sandbox and it is not obvious whether the bug lives in scene lighting, MToon material settings, or the mesh itself.

## 1. Symptom Split

### Global lighting problem

Signs:

- skin, hair, clothes, and accessories are all washed out
- edge glow changes everywhere when fill or rim lights change
- background and avatar both drift together

First move:

- inspect the scene lighting rig
- reduce fill and rim before touching materials

### Cloth or dress material problem

Signs:

- legs or skin shade correctly but dress or cloth does not
- the dark side of clothing is pale or white
- under-breast or side panels look bright instead of shadowed
- global light tweaks help a little but never fix the bad cloth banding

First move:

- inspect the live `.vrm` material settings
- compare broken cloth against a correctly shaded body material

### Mesh normals problem

Signs:

- one mesh stays wrong after material settings are reasonable
- the issue survives light tuning and cloth shade-color fixes
- the bad band follows a specific topology seam

First move:

- inspect normals on the affected mesh only
- do not keep applying broader lighting fixes

## 2. High-Value MToon Fields

The most useful problem fields for this workflow are:

- `doubleSided`
- `shadeColorFactor`
- `giEqualizationFactor`
- `matcapFactor`
- `rimLightingMixFactor`
- `parametricRimLiftFactor`
- `parametricRimColorFactor`
- `shadingToonyFactor`
- `shadingShiftFactor`

Red flags for cloth materials:

- `doubleSided: true`
- `rimLightingMixFactor` near `1`
- `matcapFactor` near `[1, 1, 1]`
- `giEqualizationFactor` near `1`
- `shadeColorFactor` near white while the dress color is dark
- very high `shadingToonyFactor` with pale shade colors

## 3. Known Fix Pattern

When cloth materials are the problem:

1. detect cloth materials by name
   - `cloth`
   - `dress`
   - `onepiece`
   - `skirt`
   - `bottoms`
   - `uniform`
   - `outfit`
2. force them to `FrontSide`
3. zero or nearly zero rim lighting
4. zero matcap contribution
5. reduce GI equalization
6. copy the cloth base color into `shadeColorFactor`
7. darken the copied shade color hard so the dark side reads dark

That pattern fixes the specific class of bug where the dress looks inside-out while the legs still shade correctly.

## 4. Verify Against a Good Material

Do not inspect broken cloth in isolation. Always compare it against at least one material that already shades correctly, usually:

- skin
- body
- legs
- stockings

If the good material and bad cloth differ mostly in MToon rim, matcap, GI, or shade-color settings, stay in the material lane.

## 5. Rebuild Discipline

The only trustworthy test is the packaged app after rebuild:

1. stop the running app
2. repack the desktop app
3. relaunch through `explorer.exe`
4. confirm health is green
5. inspect the live viewport again
