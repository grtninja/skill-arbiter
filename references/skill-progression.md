# Skill Progression and Leveling

This file tracks maturity levels for long-lived core skills.

## Level Rubric

1. Level 1: functional baseline with one deterministic path.
2. Level 2: explicit scope boundary and fail-closed behavior.
3. Level 3: evidence contract and reproducible outputs.
4. Level 4: multi-mode operation (for example normal + incident/working-tree lanes).
5. Level 5: integrated into default chain with measurable governance impact.
6. Level 6+: stable, repeatedly validated, and used as a hub or policy anchor.

## Current Core Levels

| Skill | Level | Notes |
| --- | --- | --- |
| `skill-hub` | 8 | Primary routing hub with chain contract, loopback, and lane policy controls. |
| `usage-watcher` | 7 | Deterministic usage analysis, planning, and explicit mode-selection rubric. |
| `skill-cost-credit-governor` | 7 | Policy-grade spend/chatter actions with artifacted decisions. |
| `skill-cold-start-warm-path-optimizer` | 7 | Cold/warm analysis plus prewarm/never-auto decision controls. |
| `skill-installer-plus` | 7 | Plan/admit/feedback/show loop with arbiter + trust ingestion evidence. |
| `code-gap-sweeping` | 7 | Cross-repo deterministic gap discovery with triage mapping and diff modes. |
| `request-loopback-resume` | 7 | Interruption-safe lane state model with strict resume contract. |
| `skill-auditor` | 6 | Deterministic classification and finding severity gate. |
| `skill-enforcer` | 6 | Cross-repo policy alignment gate in default chain. |
| `safe-mass-index-core` | 6 | Large-repo discovery lane with bounded, low-churn behavior. |
| `playwright-edge-preference` | 3 | New Edge-channel execution lane; deterministic fail-closed policy. |

## Level-Up Evidence Requirements

To level up a skill, capture all applicable evidence:

1. `skill-arbiter` admit evidence (`action`, `persistent_nonzero`, `max_rg`).
2. `skill-auditor` classification and findings for changed skill set.
3. Dependency/overlap improvements when scope or routing changes.
4. Updated docs in lockstep for policy-visible changes.
5. Usage/cost/cold-warm artifacts for chain-affecting changes.

## Maintenance Rule

Update this file whenever:

1. Core skill behavior materially changes.
2. Chain policy changes affect maturity expectations.
3. New evidence upgrades a skill's practical level.
