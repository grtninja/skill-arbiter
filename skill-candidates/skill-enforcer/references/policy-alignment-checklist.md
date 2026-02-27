# Policy Alignment Checklist

1. List all touched repositories and changed lanes.
2. Read each repository's `AGENTS.md` and `BOUNDARIES.md` (when present).
3. Verify command/gate requirements per repo:
   - validation commands,
   - preflight requirements,
   - release-hygiene rules,
   - privacy constraints.
4. Confirm shared contracts are compatible:
   - endpoint shapes,
   - schema keys,
   - fail-closed behavior.
5. Confirm policy-doc lockstep updates are complete for any changed workflow rules.
6. Emit a single pass/fail decision with blockers and required follow-up actions.
