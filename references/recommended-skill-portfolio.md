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
   - Run read-only local `/api/agent` bridge tasks with strict validation and bounded indexing before model-heavy workflows.
   - Trigger examples: "local bridge guidance", "credit-first repo-b orchestration", "fail-closed bridge hints"
10. `repo-b-mcp-comfy-bridge` (repo-b specific)
   - Run loopback-only MCP adapter and `shim.comfy.*` diagnostics with strict validation and fail-closed behavior.
   - Trigger examples: "comfy resource health check", "mcp comfy diagnostics", "fail-closed comfy orchestration"
11. `skill-cost-credit-governor`
   - Track per-skill spend/runtime and emit warn/throttle/disable actions when anomalies or budget pressure appear.
   - Trigger examples: "govern skill spend", "detect chatter loops", "budget enforcement policy"
12. `skill-dependency-fan-out-inspector`
   - Build dependency graphs and flag fan-out/cycle/N+1 risks across skill stacks.
   - Trigger examples: "map skill dependencies", "detect invocation fan-out", "find circular skill chains"
13. `skill-cold-start-warm-path-optimizer`
   - Measure cold-vs-warm latency and generate prewarm plus never-auto-invoke plans.
   - Trigger examples: "optimize cold starts", "build warm-path plan", "latency prewarm candidates"
14. `skill-blast-radius-simulator`
   - Simulate pre-admission blast radius and require acknowledgement for high-risk deltas.
   - Trigger examples: "simulate skill install risk", "preflight new skill risk", "blast radius gate"
15. `skill-trust-ledger`
   - Maintain local reliability memory and trust tiers from observed outcomes and arbiter evidence.
   - Trigger examples: "skill reliability ledger", "trust-tier report", "should we re-enable this skill?"
16. `skills-cross-repo-radar`
   - Run recurring cross-repo MX3/shim drift scans and map signals to skill upgrade/discovery actions.
   - Trigger examples: "scan my repos for new skill opportunities", "weekly mx3 shim skill review", "cross-repo drift check"
17. `skill-common-sense-engineering`
   - Apply lightweight human common-sense checks to catch avoidable mistakes and artifact hygiene issues.
   - Trigger examples: "quick sanity pass", "common-sense review before finalizing", "catch obvious mistakes"
18. `skill-auditor`
   - Audit newly added or recently changed skills and produce concrete upgrade/consolidation actions.
   - Trigger examples: "audit new skills", "review skill quality", "find skill consolidation opportunities"
19. `skill-enforcer`
   - Enforce required baseline skill references across repos and fail on policy drift.
   - Trigger examples: "enforce skill policy across repos", "check required skills in AGENTS/README", "compliance scan"
20. `skill-installer-plus`
   - Plan local skill installs, run lockdown admission wrappers, and learn from install outcomes.
   - Trigger examples: "install skills safely", "run admission with history", "improve install recommendations"
21. `skill-hub`
   - Route any task to an ordered skill chain with rationale and baseline common-sense checks.
   - Trigger examples: "route this task to the right skills", "start with skill hub", "build skill chain for request"
22. `multitask-orchestrator`
   - Split independent lanes into parallel execution and merge deterministic results.
   - Trigger examples: "parallelize this request", "run independent checks together", "multi-lane execution"

Legacy compatibility wrapper:
- `repo-b-local-comfy-orchestrator` is kept for existing prompt routes and should delegate to `repo-b-mcp-comfy-bridge`.

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
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --promote-safe
```

Use deny-by-default for third-party skills unless explicitly promoted.

For personal repositories, run with `--personal-lockdown` to force local-only admission and immutable pinning.

Mass-index skill admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  safe-mass-index-core repo-b-mass-index-ops repo-d-mass-index-ops repo-c-mass-index-ops \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

Meta-governance admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-cost-credit-governor skill-dependency-fan-out-inspector \
  skill-cold-start-warm-path-optimizer skill-blast-radius-simulator skill-trust-ledger \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

Cross-repo radar admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skills-cross-repo-radar \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

Common-sense baseline admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-common-sense-engineering \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

Governance system admission template:

```bash
python3 "$CODEX_HOME/skills/skill-arbiter/scripts/arbitrate_skills.py" \
  skill-hub skill-installer-plus skill-auditor skill-enforcer \
  --source-dir skill-candidates \
  --window 10 --baseline-window 3 --threshold 3 --max-rg 3 \
  --personal-lockdown
```

Natural chaining defaults:

1. Start with `skill-hub`.
2. Run `skill-installer-plus` for install/admission planning and evidence capture.
3. If chain has independent lanes, add `multitask-orchestrator`.
4. For new/updated skills, require `skill-auditor` classification (`unique` or `upgrade`).
5. For new/updated skills, require arbiter evidence and pass status before admission.
6. Loop unresolved lanes back through `skill-hub` until convergence/max loops.
7. Record XP/levels with `python3 scripts/skill_game.py` using arbiter/auditor evidence paths.

## Success Metrics

1. Mean time to unblock CI failures.
2. PRs merged without post-merge rollback/hotfix.
3. Percentage of dependency PRs merged with explicit compatibility notes.
4. Percentage of release-impacting PRs with correct version/changelog updates.
5. Skill arbitration pass/fail rate for new candidate skills.
