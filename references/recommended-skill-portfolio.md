# Recommended Cross-Repo Skill Portfolio

Use this as the default skill stack for new and existing repositories.
Goal: reduce repeated operational work while keeping behavior deterministic and safe.

## Core Skills (Install Everywhere)

1. `repo-intake-and-map`
   - Build a fast map of repo structure, build/test commands, risk surfaces, and ownership files.
   - Trigger examples: "onboard this repo", "map this codebase", "where should I change X?"
2. `release-hygiene`
   - Enforce version/changelog/tag hygiene before PR merge.
   - Trigger examples: "prepare release", "bump version", "release notes", "pre-PR release check"
3. `ci-failure-triage`
   - Normalize failing CI logs into root cause + minimal fix plan.
   - Trigger examples: "fix CI", "why did this workflow fail?", "unblock PR checks"
4. `pr-risk-review`
   - Review diffs for regression, behavior drift, missing tests, and migration risk.
   - Trigger examples: "review this PR", "find risks", "what could break?"
5. `dependency-update-safety`
   - Gate dependency bumps with compatibility checks, changelog scan, and rollback notes.
   - Trigger examples: "update deps", "dependabot PR review", "safe package bump"
6. `security-quick-audit`
   - Run lightweight checks for secret exposure, subprocess risk, path traversal, and policy drift.
   - Trigger examples: "security review", "pre-release security pass", "scan this change"
7. `docs-alignment-lock`
   - Keep AGENTS/README/CONTRIBUTING/SKILL/PR-template policy guidance aligned and privacy-safe.
   - Trigger examples: "align docs", "policy drift check", "pre-PR docs gate"
8. `usage-watcher`
   - Analyze burn rate, project usage, and set budget/rate-limit guardrails before high-volume work.
   - Trigger examples: "reduce credits usage", "set usage budget", "avoid rate limits"
9. `repo-b-local-bridge-orchestrator` (repo-b specific)
   - Run read-only local bridge tasks with strict validation and bounded indexing before model-heavy workflows.
   - Trigger examples: "local bridge guidance", "credit-first repo-b orchestration", "fail-closed bridge hints"
10. `repo-b-local-comfy-orchestrator` (repo-b specific)
   - Run loopback-only read-only Comfy MCP resource orchestration with strict validation and fail-closed diagnostics+hints.
   - Trigger examples: "comfy resource health check", "local comfy hints", "fail-closed comfy orchestration"

## Optional Skills by Repo Type

1. Backend/API repos: `api-contract-change-guard`
2. Frontend repos: `ui-regression-and-a11y`
3. Data/ETL repos: `data-migration-and-backfill-guard`
4. Infra/Terraform repos: `infra-plan-risk-gate`
5. SDK/library repos: `semver-and-breaking-change-gate`
6. Very large monorepos: `safe-mass-index-core` (+ repo wrappers such as `repo-b-mass-index-ops`, `repo-c-mass-index-ops`, `repo-d-mass-index-ops`)

## Design Rules for Every Skill

1. Keep `SKILL.md` lean; move heavy detail into `references/`.
2. Add scripts for repetitive/fragile steps (`scripts/`), not prose-only workflows.
3. Require deterministic outputs:
   - pass/fail decision
   - concise evidence
   - explicit next action
4. Include safe mode flags (`--dry-run`, non-destructive defaults) when file mutation is possible.
5. Ensure each skill can point to concrete file paths and line numbers in findings.

## Rollout Sequence (Recommended)

1. Ship `release-hygiene` and `ci-failure-triage` first.
2. Add `pr-risk-review` once CI is stable.
3. Add `dependency-update-safety` and `security-quick-audit`.
4. Add one repo-type-specific skill only after the core set is clean.

## Governance with `skill-arbiter`

Admit new skills one-by-one and promote only after clean churn behavior:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  release-hygiene ci-failure-triage pr-risk-review dependency-update-safety security-quick-audit \
  --window 10 --threshold 3 --max-rg 3 \
  --promote-safe
```

Use deny-by-default for third-party skills unless explicitly promoted.

For personal repositories, run with `--personal-lockdown` to force local-only admission and immutable pinning.

Mass-index skill admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  safe-mass-index-core repo-b-mass-index-ops repo-d-mass-index-ops repo-c-mass-index-ops \
  --source-dir skill-candidates \
  --window 10 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

## Success Metrics

1. Mean time to unblock CI failures.
2. PRs merged without post-merge rollback/hotfix.
3. Percentage of dependency PRs merged with explicit compatibility notes.
4. Percentage of release-impacting PRs with correct version/changelog updates.
5. Skill arbitration pass/fail rate for new candidate skills.
