---
name: dated-version-tracking
description: Use this skill whenever work depends on current, latest, default, recently changed, versioned, dependency, rollout, or past-context assumptions. It creates timestamped evidence for model/dependency assumptions and prior user requests so stale context can be confirmed, refreshed, rejected, or superseded later.
---

# Dated Version Tracking

## Purpose

Use this skill to stop timeless assumptions from drifting into active work. Every version-sensitive claim or recalled user request gets an absolute timestamp, evidence source, freshness rule, and status.

Default ledger:

```text
%USERPROFILE%\.codex\workstreams\dated-version-context-ledger.jsonl
```

Use `scripts/dated_context_ledger.py` for append, validation, scan, and summary operations.
Use `scripts/catalog_config_stale.py` to classify and materialize `.codex\config.stale` evidence buckets without moving live config files or active runtime state.
Use `scripts/inventory_codex_home.py` to classify `.codex` root ownership before cleanup.
Use `references/online-grounding.md` when this skill needs the external-doc basis for config, sandbox, and VS Code profile safety rules.

## When To Use

Use this skill when the request mentions:

- current, latest, default, today, yesterday, last week, last Tuesday, recently, released, rollout, migration, dependency, config, model, extension, package, CLI, API, MCP, VS Code profile, or Codex behavior
- prior context, previous fix context, another thread, memory, transcript recovery, old instructions, stale assumptions, or "I asked for this before"
- a versioned value that could have changed, including OpenAI model IDs, Codex config keys, VS Code settings, extension versions, Python paths, local endpoint contracts, schemas, and skill defaults

## Required Record Shape

Every durable record needs:

- `kind`: `version_assumption`, `dependency_assumption`, `context_request`, `context_fact`, or `stale_check`
- `subject`: the thing being remembered or assumed
- `claim`: the exact operational claim, in plain language
- `source`: where the claim came from, such as `user`, `official_docs_web`, `local_config`, `transcript`, `memory`, or `repo`
- `source_time`: absolute timestamp for the source event when known
- `recorded_at`: when this ledger entry was written
- `status`: `active`, `unverified`, `stale`, `superseded`, or `rejected`
- `confidence`: `high`, `medium`, or `low`
- `freshness_rule`: how to know when this needs re-checking

For version or dependency assumptions, also include:

- `effective_date`
- `verified_date`
- `evidence`
- `stale_if`
- `refresh_after` or `expires_at`

For user-request or prior-context records, also include:

- `requested_at`
- `resolved_time_reference` when the user used a relative phrase
- `valid_until` or a clear `freshness_rule`

## Workflow

1. Anchor the clock with the current absolute date and timezone.
2. Convert relative user timing into an absolute date/time before relying on it. Preserve the original phrase too.
3. Classify the record: version/dependency assumption, context request, context fact, or stale check.
4. Verify drift-prone claims against the freshest safe source before acting. Use official docs for upstream product behavior and local files/processes for local stack behavior.
5. Append or update the ledger before treating the claim as durable.
6. When reading old context, check `status`, `refresh_after`, `expires_at`, and `stale_if` before applying it to the current task.
7. If the old claim conflicts with live evidence, write a new `stale_check` or `superseded` record instead of silently following it.

For config, sandbox, profile, sync, model, or extension-version work, check official docs before changing durable defaults. Prefer OpenAI docs for Codex behavior and VS Code docs for profile/settings/sync behavior. See `references/online-grounding.md`.

## Read-only Guard

Treat all config, sandbox, and profile files as read-only unless every relevant gate passes.

Read-only surfaces include:

- `%USERPROFILE%\.codex\config.toml`
- `%USERPROFILE%\.codex\config.stale\**`
- `%USERPROFILE%\.codex\.sandbox`
- `%USERPROFILE%\.codex\.sandbox.broken`
- `%USERPROFILE%\AppData\Roaming\Code\User\settings.json`
- `%USERPROFILE%\AppData\Roaming\Code\User\profiles\*\settings.json`
- `%USERPROFILE%\AppData\Roaming\Code\User\globalStorage\storage.json`

Required gates before any write, move, or promotion:

1. Write a `.codex` root inventory.
2. Run the intended cleanup/config operation in `--dry-run`.
3. Prove the live config parses and still has `model = "gpt-5.5"`, `review_model = "gpt-5.5"`, `model_reasoning_effort = "xhigh"`, `profile = "starframe"`, no required MCP server, and no forbidden provider override.
4. Confirm the action excludes active runtime state: auth, live config, active SQLite/WAL/SHM, sessions, logs, and current `.sandbox`.
5. Record the dated assumption or context request in the ledger.
6. For VS Code/profile edits, back up the exact file, write a candidate, validate JSON, then promote.
7. For sandbox cleanup, only `.sandbox.broken` may move automatically; current `.sandbox` is read-only unless the user explicitly authorizes a sandbox reset.

## Context Recovery Rule

Past requests are evidence, not timeless commands. If the user says "I asked for this last Tuesday," resolve that to an absolute date using the current session date, search the relevant transcript/memory surfaces, and record:

- what was asked
- when it was asked
- where it was found
- whether it is still valid now
- what evidence would make it stale

If the timestamp cannot be proven, mark the record `unverified` with `confidence = "low"` and keep looking before using it as authority.

## Commands

Validate the ledger:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\dated_context_ledger.py validate
```

Append a version assumption:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\dated_context_ledger.py append `
  --kind version_assumption `
  --subject "Codex main model default" `
  --claim "STARFRAME Codex main lane uses gpt-5.5 xhigh." `
  --source "official_docs_web+user" `
  --source-time "2026-04-24T14:50:00-04:00" `
  --effective-date "2026-04-23" `
  --verified-date "2026-04-24" `
  --evidence "https://developers.openai.com/api/docs/models" `
  --stale-if "gpt-5.4 is treated as latest/default/main-lane after 2026-04-23" `
  --refresh-after "2026-04-25" `
  --freshness-rule "Re-check official OpenAI docs before changing model defaults."
```

Append a recovered user request:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\dated_context_ledger.py append `
  --kind context_request `
  --subject "Prior user request" `
  --claim "User asked to make dated version tracking a skill." `
  --source "current_thread" `
  --source-time "2026-04-24T14:54:00-04:00" `
  --requested-at "2026-04-24T14:54:00-04:00" `
  --freshness-rule "Still valid until superseded by user or replaced by validated skill admission."
```

Scan active surfaces for stale phrases:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\dated_context_ledger.py scan `
  --path %USERPROFILE%\.codex\config.toml `
  --pattern "Main Codex lane must start on gpt-5.4"
```

Catalog `.codex` config lineage into the user-created `config.stale` buckets:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\inventory_codex_home.py --write
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --dry-run --require-preflight
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --require-preflight
```

This writes:

```text
%USERPROFILE%\.codex\config.stale\manifest.json
%USERPROFILE%\.codex\config.stale\Current Config\
%USERPROFILE%\.codex\config.stale\Past Good Configs\
%USERPROFILE%\.codex\config.stale\Broken Configs\
```

`--materialize` copies only. `--organize` copies the live config snapshot, then moves only non-live `config.toml*` backups/failures and explicitly broken artifacts into `config.stale`.

Inventory `.codex` ownership:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\inventory_codex_home.py --write
```

This writes:

```text
%USERPROFILE%\.codex\config.stale\codex-home-inventory.json
```

Use the inventory before broad cleanup to separate Codex-native required files, STARFRAME-added surfaces, active runtime state, stale evidence, broken evidence, and unknown items that need review.

## Safety

- Do not edit `%USERPROFILE%\.codex\memories\MEMORY.md`; log dated context in the JSONL ledger or repo-owned docs instead.
- Do not treat bundled docs, old rollouts, backups, or memory snippets as current when a dated ledger entry says they are stale or unverified.
- Do not mark a version claim `active` unless it has a source and a refresh rule.
- Prefer `superseded` over deletion. Old wrong claims are useful as regression traps.
- Treat `.codex\config.stale` as evidence, not source of truth. Only `%USERPROFILE%\.codex\config.toml` is live unless the user explicitly promotes a candidate.
- Never move active runtime files: `auth.json`, `config.toml`, `state_*.sqlite*`, `logs_*.sqlite`, `*.sqlite-wal`, `*.sqlite-shm`, `sessions`, `logs`, `.sandbox`, or the current VS Code/Codex process state.
- Before broad `.codex` cleanup, write a root inventory and only move items whose category is `stale-evidence` or `broken-evidence`.
- If a script has `--require-preflight`, use it for write/move operations. Do not bypass it to make cleanup faster.
