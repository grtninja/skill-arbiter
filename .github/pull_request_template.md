## Summary

Describe what changed and why.

## Validation

- [ ] `python scripts/arbitrate_skills.py --help`
- [ ] `python scripts/nullclaw_agent.py --help`
- [ ] `python scripts/generate_skill_catalog.py`
- [ ] `python scripts/generate_skillhub_alignment.py`
- [ ] `python scripts/check_private_data_policy.py`
- [ ] `python scripts/check_external_review_hygiene.py`
- [ ] `python scripts/check_public_release.py`
- [ ] `pytest -q`
- [ ] `python -m py_compile scripts/arbitrate_skills.py scripts/check_private_data_policy.py scripts/check_external_review_hygiene.py scripts/check_public_release.py scripts/generate_skill_catalog.py scripts/nullclaw_agent.py scripts/nullclaw_desktop.py scripts/prepare_release.py scripts/check_release_hygiene.py skill_arbiter/about.py skill_arbiter/external_review_hygiene.py skill_arbiter/meta_harness_policy.py skill_arbiter/public_readiness.py skill_arbiter/self_governance.py`
- [ ] Release metadata updated for release-impacting changes (`python scripts/prepare_release.py --part patch`)
- [ ] Docs updated if behavior changed
- [ ] `AGENTS.md`, `BOUNDARIES.md`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `SKILL.md` are aligned
- [ ] `docs/PROJECT_SCOPE.md` and `docs/SCOPE_TRACKER.md` are aligned
- [ ] `references/skill-catalog.md` regenerated for inventory or source changes
- [ ] `references/skillhub-alignment-matrix.md` and `references/skillhub-source-ledger.md` regenerated when SkillHub or marketplace alignment changed
- [ ] `references/usage-chaining-multitasking.md` updated when chaining or live-ops behavior changed
- [ ] `references/vscode-skill-handling.md` updated when baseline/overlay handling changed
- [ ] `references/skill-progression.md` updated when core-skill maturity changed
- [ ] Confirmed built-ins remain additive and upstream
- [ ] Confirmed no private repo names, usernames, or absolute private paths entered repo-tracked files
- [ ] Confirmed public support links are copy-only in the desktop UI and no browser-launch behavior was added
- [ ] For source-risk changes: `references/OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md` and `references/third-party-skill-attribution.md` updated as needed
- [ ] If touching `skill-candidates/**/SKILL.md` or adjacent references: reviewed trigger language, scope boundary, loopback/escalation/approval semantics, and example assumptions as behavior-governing surfaces
- [ ] If this is an external-style skill-doc PR: confirmed no `.github/workflows` changes, no secret/config/package/runtime/script changes unless explicitly requested, and no generated-file edits without source-of-truth updates

## Risk Notes

Call out any behavior changes related to:

- quarantine/admission policy
- destructive operator confirmations
- local advisor model behavior
- loopback API surface
- self-governance and privacy gates
