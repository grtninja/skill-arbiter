## Summary

Describe what changed and why.

## Validation

- [ ] `python3 scripts/arbitrate_skills.py --help`
- [ ] `python3 scripts/check_private_data_policy.py`
- [ ] `python3 -m py_compile scripts/arbitrate_skills.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py`
- [ ] Release metadata updated for release-impacting changes (`python3 scripts/prepare_release.py --part patch`)
- [ ] Docs updated if behavior changed
- [ ] `AGENTS.md`, `README.md`, and `CONTRIBUTING.md` are aligned with policy changes
- [ ] If skills were added/updated, response text includes: `New Skill Unlocked` + `<Skill Name> leveled up to XX`

## Risk Notes

Call out any behavior changes related to process sampling, deletion, blacklisting, or repo source trust.
