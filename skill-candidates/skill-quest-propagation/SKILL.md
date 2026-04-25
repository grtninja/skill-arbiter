---
name: "skill-quest-propagation"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Propagate a governed quest across workstream state, next-quest handoff notes, and shared branch aliases. Use when a new local workflow must survive interruption and stay visible to PC Control, Continue, Codex, or VRM lanes."
---

# Skill Quest Propagation

Use this skill when a request needs a durable quest shape instead of an ad hoc note.

## Workflow

1. Harvest prior quest history into the quest registry before declaring a quest stable or resuming after interruption.
2. Name the quest and keep the objective in one sentence.
3. Define the ordered lanes before execution starts.
4. Initialize or update a deterministic workstream state file.
5. Mirror the current objective, lanes, evidence paths, and next action into the active quest handoff note.
6. Rebuild the quest registry after every meaningful lane transition so historical and active quest state stay together.
7. When the workflow introduces a new routing lane, confirm the relevant branch-alias and skill-alias surfaces expose it.
8. Re-run the resume action after interruptions before taking the next mutating step.

## Canonical Surfaces

- workstream state: `%USERPROFILE%\.codex\workstreams\*.json`
- quest handoff: `<PRIVATE_REPO_ROOT>\reports\<date>\next_quest.md`
- quest registry JSON: `references/quest-registry.generated.json`
- quest registry markdown: `references/quest-registry.generated.md`
- shared skill aliases: `<PRIVATE_REPO_ROOT>\config\vscode_surface\sidecars\skill-chain-aliases.json`
- branch aliases: `<PRIVATE_REPO_ROOT>\config\vscode_surface\sidecars\starframe-branch-aliases.json`

## Canonical Commands

Harvest prior quest state and handoff notes into the local registry:

```bash
python3 <SKILL_ARBITER_REPO>/skill-candidates/skill-quest-propagation/scripts/build_quest_registry.py \
  --reports-root <PRIVATE_REPO_ROOT>/reports \
  --workstreams-root %USERPROFILE%/.codex/workstreams
```

Initialize a quest state file:

```bash
python3 <SKILL_ARBITER_REPO>/skill-candidates/request-loopback-resume/scripts/workstream_resume.py \
  init \
  --state-file %USERPROFILE%/.codex/workstreams/example-quest.json \
  --task "Example governed workflow" \
  --lane "reference curation" \
  --lane "generation batch" \
  --lane "local refinement" \
  --lane "workbench handoff"
```

Update quest state after a lane transition:

```bash
python3 <SKILL_ARBITER_REPO>/skill-candidates/request-loopback-resume/scripts/workstream_resume.py \
  set \
  --state-file %USERPROFILE%/.codex/workstreams/example-quest.json \
  --lane-status "reference curation=completed" \
  --lane-status "generation batch=in_progress" \
  --lane-next "generation batch=Generate the next keeper batch and open previews locally" \
  --artifact %USERPROFILE%/.codex/workstreams/example-artifact.json
```

Compute the deterministic next step:

```bash
python3 <SKILL_ARBITER_REPO>/skill-candidates/request-loopback-resume/scripts/workstream_resume.py \
  resume \
  --state-file %USERPROFILE%/.codex/workstreams/example-quest.json \
  --json-out %USERPROFILE%/.codex/workstreams/example-quest-resume.json
```

## Required Evidence

- quest registry JSON and markdown with a fresh `generated_at`
- quest objective and ordered lanes
- current state file path
- latest resume JSON or equivalent next-step proof
- current next-quest handoff path
- branch or skill alias proof if the quest depends on a new routed workflow lane

## Guardrails

- Do not leave a governed workflow with no state file.
- Do not leave previous quest history only in transient local files when the registry can be rebuilt.
- Do not mark a lane complete without a concrete artifact or verification note.
- Do not let the quest handoff drift from the workstream state.
- Do not skip the registry rebuild after a meaningful quest update or recovery pass.
- Do not add a new routed workflow lane without updating the alias source of truth.

## Best-Fit Companion Skills

- `$skill-hub`
- `$request-loopback-resume`
- `$skill-common-sense-engineering`
- `$skill-auditor`
- `$skill-arbiter-lockdown-admission`

## References

- `references/quest-checklist.md`
- `references/quest-registry.md`

## Scope Boundary

Use this skill for quest shaping, propagation, quest-history harvesting, and resume-safe visibility.

Do not use it for:

1. repo-specific implementation details
2. media rendering internals
3. generic meeting or note-taking tasks

## Loopback

If the quest loses deterministic next-step evidence:

1. capture the latest state file and resume JSON
2. rebuild the quest registry and verify the active handoff note reflects the same next action
2. route back through `$skill-hub`
3. continue only after the updated quest lane order is explicit
