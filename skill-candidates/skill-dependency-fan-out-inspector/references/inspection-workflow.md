# Inspection Workflow

## Inputs

- Skills root directory (default: `skill-candidates`)
- Optional skill filters (`--skill` repeated)
- Risk thresholds:
  - fan-out threshold
  - transitive reach threshold

## Steps

1. Discover skill folders containing `SKILL.md`.
2. Parse explicit dependency references (`$skill-name`).
3. Compute:
   - in-degree / out-degree
   - transitive reach
   - cycle sets
4. Classify risks:
   - fan-out hotspot
   - N+1 reach risk
   - cycle risk
5. Emit JSON + optional DOT outputs.

## Practical Uses

- Pre-merge review of new skill bundles.
- Monthly portfolio hygiene review.
- Root-cause analysis for unexpected invocation cascades.
