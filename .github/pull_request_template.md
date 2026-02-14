## Summary

Describe what changed and why.

## Validation

- [ ] `python3 scripts/arbitrate_skills.py --help`
- [ ] `python3 scripts/skill_game.py --help`
- [ ] `python3 scripts/check_private_data_policy.py`
- [ ] `python3 -m py_compile scripts/arbitrate_skills.py scripts/skill_game.py scripts/prepare_release.py scripts/check_release_hygiene.py scripts/check_private_data_policy.py`
- [ ] Release metadata updated for release-impacting changes (`python3 scripts/prepare_release.py --part patch`)
- [ ] Docs updated if behavior changed
- [ ] `AGENTS.md`, `README.md`, and `CONTRIBUTING.md` are aligned with policy changes
- [ ] For skill-system changes: `skill-hub` routing plus `skill-installer-plus` plan/admit evidence captured where applicable
- [ ] For skill-system changes: `usage-watcher` analysis/plan evidence captured and chaining mode (`economy`/`standard`/`surge`) documented
- [ ] For skill-system changes: `skill-cost-credit-governor` analysis/policy evidence captured and any `warn`/`throttle`/`disable` actions documented
- [ ] For skill-system changes: `skill-cold-start-warm-path-optimizer` analysis/plan evidence captured and prewarm decision documented
- [ ] For multi-repo skill-system changes: `code-gap-sweeping` report captured with JSON evidence path
- [ ] For interrupted/resumed workstreams: `request-loopback-resume` state + resume JSON evidence path captured
- [ ] For skill-system changes: `scripts/skill_game.py` score event recorded with arbiter/auditor evidence paths
- [ ] For multi-lane work: `multitask-orchestrator` usage and `skill-hub` loopback behavior documented
- [ ] For new/updated skills: attach `skill-arbiter-lockdown-admission` evidence (`action`, `persistent_nonzero`, `max_rg`) from `--json-out`
- [ ] For new/updated skills: attach `skill-installer-plus` plan/admit outputs (decision, score, arbiter JSON path)
- [ ] For new/updated skills: include `skill-auditor` classification (`unique` or `upgrade`) and nearest-peer rationale
- [ ] For `upgrade` classifications: document why existing skill update was chosen (or justify a new split lane)
- [ ] If skills were added/updated, response text includes: `New Skill Unlocked: <SkillName>` + `<SkillName> Leveled up to <LevelNumber>`

## Risk Notes

Call out any behavior changes related to process sampling, deletion, blacklisting, or repo source trust.
