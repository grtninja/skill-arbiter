# Workflow Notes

## Inputs

- VRoid Studio install bundle: `VRoidStudio_Data/data.unity3d`
- AssetRipper Unity export project containing Photo Booth `.anim` clips
- Local UniVRM source tree (for example `univrm-0.128.0/Assets`)
- Unity Editor executable

## Clip Roots

Default export roots:

1. `Assets/Resources/animations/female`
2. `Assets/Resources/animations/male`
3. `Assets/Resources/animations/pv/female`
4. `Assets/Resources/animations/pv/male`

## Deterministic Outputs

- One `.vrma` per source `.anim` clip.
- `vrma_export_summary.tsv` with `ok/failed` status rows.
- Output validation that checks:
  - summary has zero `failed` rows,
  - every `.vrma` includes `VRMC_vrm_animation` marker.

## Naming

Output clip naming uses:

- folder prefix from `Assets/Resources/animations/*`
- original clip name

Pattern:

- `<folder-prefix>__<clip-name>.vrma`
