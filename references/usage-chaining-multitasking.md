# Skill Usage, Chaining, and Multitasking Guide

This guide defines how to use the current skill set safely and efficiently.

## Operating Model

1. Keep built-ins enabled as upstream defaults.
2. Add repository overlay skills from `skill-candidates/`.
3. Route tasks through deterministic chains instead of ad-hoc skill hopping.
4. Capture evidence artifacts for any changed skill, chain policy, or admission decision.

## Standard Chain (Default)

Use this sequence for most non-trivial work:

1. `skill-hub` for route selection.
2. `skill-common-sense-engineering` for baseline sanity.
3. `usage-watcher` for usage mode and budget posture.
4. `skill-cost-credit-governor` for spend/chatter controls.
5. `skill-cold-start-warm-path-optimizer` for warm-path policy.
6. `code-gap-sweeping` for cross-repo deterministic gap checks when applicable.
7. `request-loopback-resume` for interruption-safe checkpoints when needed.
8. `skill-installer-plus` for install/admission planning and recommendation memory.
9. `skill-auditor` for new/changed skill classification.
10. `skill-enforcer` for cross-repo policy alignment.

## High-Value New Capability Patterns

### Media and Asset Workflows

- `sora`: video generation/remix/list/download/delete workflows.
- `imagegen`: image generation/edit/inpaint/background workflows.
- `speech`: text-to-speech narration and batch voice generation.
- `transcribe`: speech-to-text with optional diarization.

Recommended chain:

1. `skill-hub`
2. `usage-watcher`
3. `skill-cost-credit-governor`
4. Media skill (`sora`, `imagegen`, `speech`, or `transcribe`)
5. `skill-cold-start-warm-path-optimizer` if repeated runs are expected

### Edge Browser Automation Workflows

- `playwright-edge-preference`: force Microsoft Edge channel execution.
- `playwright-safe`: low-churn guardrail lane for browser automation.
- `playwright` (built-in): broad browser automation baseline.

Recommended chain:

1. `skill-hub`
2. `playwright-edge-preference`
3. `playwright-safe` (when churn sensitivity is high)
4. `usage-watcher` + `skill-cost-credit-governor` for long-running or batch browser jobs

### Repo Governance and Safety Workflows

- `docs-alignment-lock`
- `skill-auditor`
- `skill-arbiter-lockdown-admission`
- `skill-enforcer`

Recommended chain:

1. `skill-hub`
2. `docs-alignment-lock`
3. `skill-auditor`
4. `skill-arbiter-lockdown-admission`
5. `skill-enforcer`

### Large-Repo Discovery Workflows

- `safe-mass-index-core`
- `repo-b-mass-index-ops`
- `repo-c-mass-index-ops`
- `repo-d-mass-index-ops`

Recommended chain:

1. `skill-hub`
2. Appropriate mass-index wrapper
3. `code-gap-sweeping` for multi-repo consistency checks
4. `request-loopback-resume` if work is interrupted

## Multitasking Pattern

When tasks have independent lanes, split them into explicit streams and merge only after each lane has deterministic evidence.

Lane examples:

1. Lane A: policy/docs alignment
2. Lane B: runtime bug fix
3. Lane C: skill admission/audit evidence

Lane merge rules:

1. Each lane must return pass/fail evidence and next action.
2. Blocked lanes must loop through `request-loopback-resume` or back to `skill-hub`.
3. Final merge must include conflict check across files and policy docs.

If `multitask-orchestrator` is available in your environment, use it. If not, apply the same lane split/merge policy manually.

## Evidence Artifacts to Keep

- `usage-watcher`: usage analysis + plan JSON
- `skill-cost-credit-governor`: analysis + policy JSON
- `skill-cold-start-warm-path-optimizer`: analysis + plan JSON
- `skill-arbiter-lockdown-admission`: arbiter JSON (`action`, `persistent_nonzero`, `max_rg`)
- `skill-auditor`: audit JSON (`unique`/`upgrade` + findings)
- `code-gap-sweeping`: repo findings JSON

## Guardrails

1. Do not disable built-ins to make overlay skills work.
2. Do not replace upstream built-ins with local forks in place.
3. Keep overlay skills additive and scoped.
4. Keep `references/skill-catalog.md` current after any skill change.
5. Use privacy-safe placeholders in all skill docs and references.
