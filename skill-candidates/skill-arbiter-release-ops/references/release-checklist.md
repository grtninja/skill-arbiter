# Release Ops Checklist

1. Run `prepare_release.py` for semantic version bump.
2. Edit generated changelog notes for accuracy.
3. Confirm `pyproject.toml` and top changelog version match.
4. Run `check_release_hygiene.py` before PR.
5. Keep CI checks green for all release scripts.
