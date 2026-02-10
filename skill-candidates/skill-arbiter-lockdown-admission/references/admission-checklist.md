# Lockdown Admission Checklist

1. `--source-dir` points to local candidate skills.
2. Run `scripts/artifact_hygiene_scan.py` with `--fail-on-found`.
3. If artifacts are found, run the same script with `--apply` and save cleanup evidence JSON.
4. `--personal-lockdown` is enabled.
5. `max_rg` and `persistent_nonzero` are reviewed for every candidate.
6. Failing skills are deleted/blacklisted; passing skills are pinned immutable.
7. JSON evidence is stored for reproducibility.
