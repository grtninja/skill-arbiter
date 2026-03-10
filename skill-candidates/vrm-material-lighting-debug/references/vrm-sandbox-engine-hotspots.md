# VRM Sandbox Engine Hotspots

Use these hotspots when applying the fix in `VRM-Sandbox`.

## Main File

- `packages/engine/src/index.ts`

## Hotspot Areas

### Scene lighting rig

Use this area when the whole avatar is overlit:

- ambient, directional, key, fill, and rim lights
- any avatar-light boost math tied to scene presets

### MToon compatibility pass

Use this area when cloth materials ignore sane scene lighting:

- avatar-load-time material patching
- cloth-material name detection
- rim, matcap, GI, and shade-color overrides
- outline and sidedness clamps

### Avatar load path

Confirm the MToon fix actually runs after the VRM loads. A good patch in the wrong place still leaves the live app broken.

## Live Verification Targets

- `http://127.0.0.1:5175/health`
- packaged app viewport after rebuild

## Windows Relaunch Rule

Relaunch with `explorer.exe` to avoid stray shell windows attached to the app.
