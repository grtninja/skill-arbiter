---
name: operator-language-humanizer
description: Local-first operator language cleanup for prompts, run titles, queue notes, QC summaries, and user-visible output text across local app stacks. Use when tightening wording without changing meaning, policy, IDs, paths, flags, or system behavior. This skill is explicit opt-in and must never rewrite system prompts, personality files, or hidden instructions.
---

# Operator Language Humanizer

Use this skill for cross-stack operator-facing wording cleanup only.

## Workflow

1. Treat the source text as authoritative. Preserve technical meaning and operator intent.
2. Restrict edits to user-visible operator surfaces such as:
   - run titles
   - queue notes
   - desired-result fields
   - prompt-head drafts
   - QC summaries
   - review findings
   - export or handoff text shown to an operator
3. Keep exact tokens unchanged when they carry runtime meaning:
   - file paths
   - model IDs
   - job IDs
   - port numbers
   - flags
   - API field names
4. Remove filler, AI-sounding hedges, and repetitive phrasing only when that does not change technical intent.
5. Prefer concise operator language over stylistic flourish.
6. If the requested cleanup could alter policy or hidden behavior, stop and ask for a safer visible-text target.

## Hard Guardrails

Never use this skill to rewrite or "humanize":

1. system prompts
2. agent personality files
3. hidden tool instructions
4. security or policy text
5. API contracts, schemas, or logs
6. docs-lane prose such as READMEs, blog posts, or release notes unless the user explicitly wants that handled by a docs or prose lane instead

## Local-First Rule

- Work from text already present in the workspace or supplied in the request.
- Do not depend on remote scoring APIs, telemetry, or hidden classifiers.
- Keep the output deterministic and reviewable in plain text.

## Pass Criteria

At minimum, require:

1. the cleaned text is shorter or clearer without losing operational meaning
2. all runtime-critical tokens remain exact
3. the result still sounds like an operator or tool note, not a personality rewrite
4. the change can be reviewed side by side if the wording is safety-sensitive

## Scope Boundary

Use this skill for operator or prompt/output cleanup across local stacks.

Do not use it for:

1. docs-lane polishing
2. marketing copy
3. hidden-prompt rewriting
4. personality or tone overhauls unrelated to operator clarity

## References

- `references/allowed-surfaces.md`
- `references/cleanup-checklist.md`
