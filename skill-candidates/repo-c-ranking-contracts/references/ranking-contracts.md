# Ranking Engine Contract Checklist

1. Ranking order remains deterministic for equal-score candidates.
2. Aggregate multipliers preserve quality/reliability/provenance keys.
3. Report JSON remains schema-valid against `ranking_report.schema.json`.
4. Scoring changes include updated tests.
