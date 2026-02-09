# Docs Alignment Checklist

1. `AGENTS.md` defines current policy and command requirements.
2. `README.md` and `CONTRIBUTING.md` match `AGENTS.md` wording for release + privacy gates.
3. `SKILL.md` includes current release and privacy lock commands.
4. `.github/pull_request_template.md` checks match actual required commands.
5. Skill candidate docs use placeholders instead of private repo names and absolute user paths.
6. Skill update communication rule exists and is unchanged:
   - `New Skill Unlocked`
   - `<Skill Name> leveled up to XX`
7. `python3 scripts/check_private_data_policy.py` passes.
8. `python3 scripts/check_release_hygiene.py` passes (or release bump was done if required).
