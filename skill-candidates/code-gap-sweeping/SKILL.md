---
name: code-gap-sweeping
description: Sweep one or more local repositories for implementation gaps and produce deterministic, evidence-backed remediation lanes. Use when you need cross-repo detection of missing tests, docs lockstep drift, risky TODO/FIXME additions, and release-hygiene misses.
---

# Code Gap Sweeping

Use this skill to run a repeatable cross-repo gap scan and convert findings into concrete follow-up actions.

## Workflow

1. Run the gap sweep script across one or more local repos.
2. Review severity-ranked findings (`critical`, `high`, `medium`).
3. Route each finding into the smallest existing skill lane that can fix it.
4. Emit machine-readable evidence for admission, planning, and release notes.
5. For repeated multi-repo operations, generate a deterministic repo-family command matrix.

## Canonical Run

```bash
python3 "$CODEX_HOME/skills/code-gap-sweeping/scripts/code_gap_sweep.py" \
  --repo "<PRIVATE_REPO_A>=/path/to/<PRIVATE_REPO_A>" \
  --repo "<PRIVATE_REPO_B>=/path/to/<PRIVATE_REPO_B>" \
  --since-days 14 \
  --json-out /tmp/code-gap-sweep.json
```

One-command sweep for all repos under a workspace root:

```bash
python3 "$CODEX_HOME/skills/code-gap-sweeping/scripts/code_gap_sweep.py" \
  --repos-root "$env:USERPROFILE\\Documents\\GitHub" \
  --exclude-repo "docs" \
  --since-days 14 \
  --json-out /tmp/code-gap-sweep-all.json
```

Full pipeline matrix for repo families (`repo_a`/`repo_b`/`repo_c`/`repo_d`):

```bash
python3 "$CODEX_HOME/skills/code-gap-sweeping/scripts/repo_family_pipeline.py" \
  --repo "<PRIVATE_REPO_A>=/path/to/<PRIVATE_REPO_A>" \
  --repo "<PRIVATE_REPO_B>=/path/to/<PRIVATE_REPO_B>" \
  --repo "<PRIVATE_REPO_C>=/path/to/<PRIVATE_REPO_C>" \
  --repo "<PRIVATE_REPO_D>=/path/to/<PRIVATE_REPO_D>" \
  --family "<PRIVATE_REPO_A>=repo_a" \
  --family "<PRIVATE_REPO_B>=repo_b" \
  --family "<PRIVATE_REPO_C>=repo_c" \
  --family "<PRIVATE_REPO_D>=repo_d" \
  --since-days 14 \
  --json-out /tmp/repo-family-pipeline.json \
  --bash-out /tmp/repo-family-pipeline.sh
```

## Scope Boundary

Use this skill when the primary task is detecting and prioritizing implementation gaps across repositories.

Do not use this skill for:

1. Skill install/quarantine decisions (use `skill-arbiter-lockdown-admission`).
2. Skill discovery portfolio curation (use `skills-discovery-curation`).
3. Repo-specific deep debugging where a dedicated repo skill exists.

## Gap Contracts

The script detects deterministic gap categories:

1. `tests_missing`: code changed without corresponding test changes.
2. `docs_lockstep_missing`: behavior-impacting files changed without docs updates.
3. `todo_fixme_added`: newly introduced `TODO`/`FIXME` markers in the patch window.
4. `release_hygiene_missing`: release-impacting changes without `pyproject.toml` + `CHANGELOG.md` updates.

## Output

JSON report includes:

- scan metadata (`generated_at`, `since_days`, repo list)
- per-repo findings with severity and evidence
- aggregate counters by category and severity
- suggested skill lanes for remediation

## References

- `references/gap-rubric.md`
- `scripts/code_gap_sweep.py`
- `references/repo-family-pipeline.md`
- `scripts/repo_family_pipeline.py`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the JSON report path and unresolved findings.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
