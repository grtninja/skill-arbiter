# Quest System

`skill-arbiter` uses quests to make substantial governed work readable from request to finished result.

## Definition

A quest is a bounded execution record with:

- one operator request
- one declared chain or lane family
- explicit skills used and required
- ordered steps
- checkpoints that prove progress
- a usable final outcome
- named deliverables and evidence

## Why this exists

Chains explain how work should flow.
Quests explain what actually happened and whether the result is usable.

## Quest lifecycle

1. Open from the incoming request.
2. Select the chain and required skills.
3. Execute steps.
4. Mark checkpoints as they are proved.
5. Close only when a usable outcome, deliverables, and evidence exist.

## Progress and checkpoints

- Steps are the human-readable path through the chain.
- Checkpoints are proof markers such as authority verified, bridge healthy, inventory refreshed, or docs aligned.
- A quest can be `success`, `partial`, or `failed`.
- Successful quests must include `final_outcome`, at least one deliverable, and at least one evidence item.

## XP and leveling

- Each completed quest awards per-skill quest XP to participating skills.
- The same completion also feeds cumulative agent XP through the skill game.
- High-level agent progression is the aggregate effect of many completed quests with good streak quality.

## Meta-Harness rule

Meta-Harness implementation work should be treated as quests by default.

Typical Meta-Harness checkpoints:

- authority lanes pinned to `:9000` and `:2337`
- bridge capability verified
- repo-root normalization verified
- controlled-write or guarded mode confirmed
- end-state activity visible on the intended surface
