---
name: "vrm-roundtrip-ci-gate"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Gate VRM importer/exporter changes using Blender, UniVRM, and VRM4U round-trip metrics. Use when PRs can affect bones, expressions, materials, or animation fidelity."
---

# VRM Roundtrip CI Gate

Use this skill to set up and enforce reproducible VRM round-trip checks.

## Workflow

1. Select canonical fixture VRMs and lock their checksums.
2. Run round-trip stages (Blender -> Unity/UniVRM -> Unreal/VRM4U -> Blender).
3. Compute bucketed deltas for rig, expressions, materials, and animation timing.
4. Enforce thresholds with a deterministic gate script.
5. Fail closed when any bucket exceeds limits.

## Threshold Defaults

- Bone rotation: <= 0.5 degrees per axis
- Bone position: <= 0.001 units
- Blendshape weight delta: <= 0.02
- Name/slot mismatches: immediate fail

## Commands

```bash
python3 scripts/metrics_gate.py \
  --report-json /path/to/roundtrip-report.json \
  --max-rot-deg 0.5 \
  --max-pos 0.001 \
  --max-blend 0.02
```

## References

- `references/roundtrip-buckets.md`
- `references/pin-matrix.md`

## Loopback

If gate fails:

1. Report failing bucket and fixture.
2. Block exporter/runtime promotion.
3. Re-run after targeted fix only.
