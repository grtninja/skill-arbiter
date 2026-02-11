---
name: request-loopback-resume
description: Resume previously requested work deterministically after interruptions. Use when context switches, AFK gaps, or multi-lane pauses require checkpointed state, explicit next actions, and fail-closed resume validation.
---

# Request Loopback Resume

Use this skill when you need to return to a prior request without losing execution intent.

## Workflow

1. Initialize a workstream state file with task + lanes.
2. Update lane status, next-step notes, and evidence artifacts during work.
3. Validate state before resuming (single in-progress lane rule).
4. Generate deterministic resume action (`continue`, `start`, `blocked`, `done`).

## Canonical Commands

Initialize:

```bash
python3 "$CODEX_HOME/skills/request-loopback-resume/scripts/workstream_resume.py" \
  init \
  --state-file .codex/workstreams/example.json \
  --task "Upgrade media pipeline skills" \
  --lane "skill update" \
  --lane "validation" \
  --lane "docs"
```

Update checkpoint:

```bash
python3 "$CODEX_HOME/skills/request-loopback-resume/scripts/workstream_resume.py" \
  set \
  --state-file .codex/workstreams/example.json \
  --lane-status "skill update=completed" \
  --lane-status "validation=in_progress" \
  --lane-next "validation=Run arbiter + installer evidence" \
  --artifact /tmp/repo-b-media-skills-arbiter.json
```

Resume action:

```bash
python3 "$CODEX_HOME/skills/request-loopback-resume/scripts/workstream_resume.py" \
  resume \
  --state-file .codex/workstreams/example.json \
  --json-out /tmp/workstream-resume.json
```

## Status Model

Allowed lane status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`

Rules:

1. At most one lane can be `in_progress`.
2. `resume` action is `continue` for current `in_progress` lane.
3. If no lane is `in_progress`, action is `start` for first `pending` lane.
4. If only `blocked/completed` lanes remain, action is `blocked` or `done`.

## Scope Boundary

Use this skill for resuming prior user requests and preserving deterministic continuity across interruptions.

Do not use this skill for:

1. Repo-specific implementation/debugging lanes.
2. Skill admission/classification decisions.
3. Release version/changelog operations.

## References

- `references/state-contract.md`
- `scripts/workstream_resume.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture latest `resume` JSON output.
2. Route through `$skill-hub` for chain recalculation.
3. Continue only after a deterministic next lane is selected.
