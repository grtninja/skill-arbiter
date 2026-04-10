# Tooling and Sources

Use this file when `white-hat` needs a practical shortlist of external patterns or tools. These sources are for defender-first guidance, discovery, and bounded local use only. Do not auto-install third-party skill bodies from them.

## Safe companion tooling

### Agent and prompt security

- `promptfoo/promptfoo`
  - Link: https://github.com/promptfoo/promptfoo
  - Why it helps: prompt, agent, and RAG evals; red teaming; vulnerability scanning; CI/CD integration.
- `invariantlabs-ai/invariant`
  - Link: https://github.com/invariantlabs-ai/invariant
  - Why it helps: event-stream and action guardrail patterns for secure agent development.

### Secret and credential leakage

- `Yelp/detect-secrets`
  - Link: https://github.com/Yelp/detect-secrets
  - Why it helps: baseline-driven secret detection that fits pre-commit and repo hygiene workflows.
- `trufflesecurity/trufflehog`
  - Link: https://github.com/trufflesecurity/trufflehog
  - Why it helps: verified leaked-credential hunting when exposure risk is higher than simple regex screening.

### Dependency and package exposure

- `google/osv-scanner`
  - Link: https://github.com/google/osv-scanner
  - Why it helps: practical dependency vulnerability scanning using OSV data.

## GitHub hardening lane

Use these controls when the white-hat pass includes PR governance, branch protection, or merge-risk reduction:

- Rulesets + CODEOWNERS review
  - Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
  - Why it helps: combine `Require pull request before merging`, code-owner review, status checks, code scanning results, and path restrictions in one branch governance surface.
- Required reviewer rules
  - Docs: https://github.blog/changelog/2026-02-17-required-reviewer-rule-is-now-generally-available/
  - Why it helps: require specific teams to approve changes for sensitive paths, not just generic approvers.
- Code scanning merge protection
  - Docs: https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/set-code-scanning-merge-protection
  - Why it helps: make CodeQL or another scanner a native merge blocker with alert thresholds.
- Push protection
  - Docs: https://docs.github.com/en/code-security/concepts/secret-security/about-push-protection
  - Why it helps: stop secrets before they land and audit bypasses or exemptions.
- Checks API risk gate
  - Docs: https://docs.github.com/en/rest/checks/runs
  - Why it helps: publish one required pass/fail "Risk" check from a GitHub App so PR risk signals stay centralized.

## GitHub org-governance lane

Use these controls when the white-hat pass includes contributor reduction, repo governance, or organization-wide hardening:

- Organization rulesets
  - Docs: https://docs.github.com/en/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization
  - Why it helps: apply consistent push, review, branch, and merge controls across many repositories without hand-maintaining each repo.
- Protected branches
  - Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
  - Why it helps: harden critical branches with required reviews, checks, and force-push restrictions.
- Signed commits
  - Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
  - Why it helps: require provenance on commits and reduce anonymous or spoofed change paths.
- Commit sign-off policy
  - Docs: https://docs.github.com/en/organizations/managing-organization-settings/managing-the-commit-signoff-policy-for-your-organization
  - Why it helps: add lightweight authorship attestation for web-based changes.
- Private vulnerability reporting
  - Docs: https://docs.github.com/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository
  - Why it helps: gives researchers a private disclosure path instead of forcing public issue threads.
- Organization audit log
  - Docs: https://docs.github.com/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/reviewing-the-audit-log-for-your-organization
  - Why it helps: turns member, permission, and repo events into searchable security telemetry that can be forwarded to SIEM tooling.
- OpenSSF Scorecard
  - Repo: https://github.com/ossf/scorecard
  - Why it helps: adds dependency and repository security signals that can be surfaced in CI or scheduled review lanes.

## High-value pattern sources already on disk

### OpenClaw clone

- `<external-candidate-root>/openclaw/SECURITY.md`
  - Strong maintainer-facing report template and explicit out-of-scope guidance.
- `<external-candidate-root>/openclaw/docs/security/THREAT-MODEL-ATLAS.md`
  - Useful ATLAS-shaped AI threat taxonomy for prompt injection, tool misuse, and agent exploitation.
- `<external-candidate-root>/openclaw/.detect-secrets.cfg`
  - Practical secret-scan baseline posture already used by a nearby ecosystem project.

### OpenHands clone

- `<external-candidate-root>/OpenHands/openhands/security/README.md`
  - Good model for confirmation-mode and security-analyzer lanes that can stop risky agent actions.

### NullClaw clone

- `<external-candidate-root>/nullclaw/docs/en/security.md`
  - Additional prompt-injection hardening and gateway-surface framing from a related local clone.

## SkillHub posture

- Treat SkillHub as `discovery_only`.
- Relevant patterns observed there:
  - `skill-vetter` for security-first skill vetting before install
  - `audit-agents-skills` for structured skill and agent audit scoring
- Do not install these raw into the stack from the marketplace lane. Use them only to inspire repo-owned rewrites or bounded intake review.

## Recommended discovery queries

Use these when mining GitHub, SkillHub, or local clone indexes for future `white-hat` upgrades:

- `security`
- `threat-model`
- `prompt-injection`
- `tool-guardrail`
- `secret-scan`
- `credential-leak`
- `dependency-vuln`
- `coordinated-disclosure`
- `agent-security`
- `mcp-security`
