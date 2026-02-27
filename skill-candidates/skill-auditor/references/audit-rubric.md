# Skill Audit Rubric

## Classification

- `unique`: nearest overlap score is below the configured upgrade threshold.
- `upgrade`: nearest overlap score is at or above the configured upgrade threshold.

## Severity Levels

- `high`: admission blockers (missing frontmatter fields, failed/missing required arbiter evidence).
- `medium`: important hygiene gaps (missing `agents/openai.yaml`, frontmatter-name mismatch).
- `low`: non-blocking improvements (oversized `SKILL.md`, high overlap that needs clearer boundaries).

## Required Output Fields

- `high_count`
- `medium_count`
- `low_count`
- `classifications[]` with `skill`, `classification`, `nearest_peer`, `similarity`
- `findings[]` with `skill`, `severity`, `code`, `message`

## Pass Criterion

- Admission-ready audit output requires `high_count = 0`.
