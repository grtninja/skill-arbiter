---
name: cross-machine-timeout-performance-governance
description: Audit and repair timeout, CPU churn, queue backpressure, stale process, cross-agent coordination, and newly available capability drift across Eddie's local machines while keeping each PC as its own island. Use when the user says no more timeouts, asks for performance cleanup, whole-stack audit, cross-agent steering, machine-wide behavior propagation, unfinished work recovery, or new Codex/model/tool capability audits.
---

# Cross-Machine Timeout Performance Governance

Human-facing nickname: Agentic Necromancy.

Use this skill when a lane must stop repeating timeout, CPU churn, idle-agent, or unfinished-work failures across Soundwave, Shockwave, Cybertron, or any other Eddie-owned machine.

This is a behavior skill, not permission to mix machine contexts. Each PC is audited from its own live state, configs, logs, and active operator surfaces.

## Core Rules

1. Treat every timeout as a defect, not a one-off.
2. Stop calling the timing-out path until the culprit is classified.
3. Prefer bounded probes over broad recursive scans.
4. Fix the repeatable cause before resuming the same path.
5. Keep active user-visible apps, listener owners, and operator surfaces alive unless Eddie explicitly asks otherwise.
6. Use subagents for bounded sidecar audits, and make them inherit this timeout/performance discipline.
7. Resume the original main quest after the repair; a timeout fix is not a reason to stop work.

## Timeout Repair Loop

For any timeout, hang, or repeated disconnect:

1. Capture the exact command, tool, endpoint, script, prompt, or route that stalled.
2. Stop reusing that path until one of these is true:
   - an explicit timeout/deadline was added,
   - a cheaper bounded path replaced it,
   - the stalled process was proven stale and stopped,
   - the service was proven healthy through bounded probes.
3. Add or verify:
   - per-request timeout,
   - max attempts,
   - backoff with jitter where retries exist,
   - max runtime or max passes for loops,
   - bounded file enumeration,
   - incremental cache or recent-only scan for large trees.
4. Validate with the narrowest probe that proves the fix.
5. Record the culprit and the safer path in the active workstream or final report.

## Performance Cleanup Loop

Use a culprit map before killing or restarting anything:

- `keep`: listener owners, PC Control supervisor tree, model lanes, user-visible operator apps, active launchers.
- `kill`: proven stale/orphaned helpers, duplicate unbounded loops, old temporary wrappers with no live listener ownership.
- `suspect-but-verify`: long-lived non-listener Python/Node/PowerShell, parser shells, desktop guards, local agents, heavy indexers.
- `exclude`: Explorer, visible VS Code/ChatGPT/LM Studio/operator apps, GPU control tools, unrelated system utilities unless Eddie asks.

Minimum checks:

1. Sample CPU by delta, not just total lifetime CPU.
2. Map hot processes to command lines and parent PIDs.
3. Check live listener ownership for required ports before action.
4. Stop only confirmed stale churn first.
5. Patch any loop or poller that would recreate the churn.

## Cross-Agent Steering

Main Codex agents and subagents may steer each other through evidence, but cooperation must be explicit:

1. Assign disjoint scopes before dispatch.
2. Ask explorers for findings, not edits, unless a worker has a clearly owned write set.
3. Treat subagent reports as evidence to integrate, not authority to blindly apply.
4. Before editing, recheck current file state because another agent may have changed it.
5. Do not wait on dead, missing, or idle agents when local progress is possible.
6. When another thread is working the same issue, leave coordination breadcrumbs and avoid broad restarts.
7. Subagents must use bounded probes, explicit timeouts, and culprit maps; they may not run broad recursive scans or unbounded loops by default.
8. Main agents may redirect subagents when new evidence appears, but must not duplicate the same unresolved work across multiple workers.
9. Cross-main-agent steering should happen through concrete artifacts: task lists, workstream JSON, diff-visible patches, process culprit maps, and exact file paths.
10. If another agent has already claimed or edited a surface, switch to review/integration unless the user explicitly asks for parallel implementation.

## Old Thread And Automation Steering

Old threads, auto-resume lanes, and automation workers can be steered by durable packets:

1. Write steering packets to the active workstream surface before expecting a resumed thread to inherit new behavior.
2. Include task status, exact next action, timeout/performance rules, owned files, and stop conditions.
3. Keep packets machine-local; do not import another PC's stale context as authority.
4. Treat old-thread context as stale until refreshed against live files, processes, and current user instructions.
5. Prefer resume packets over browser/thread steering when the old thread is not currently active.
6. Automation lanes must consume the same bounded-probe and culprit-map rules before dispatching work.

## Task Necromancy

Use agentic necromancy to recover unfinished or broken work without flooding the PC:

1. Inventory old unfinished tasks from workstreams, ledgers, status files, and recent continuity surfaces.
2. Score each task:
   - `active`: current user lane or hot blocker,
   - `recoverable`: enough artifacts exist to resume safely,
   - `stale`: needs live verification before action,
   - `dead`: superseded, duplicated, or unsafe to revive.
3. Revive only one bounded slice per task at a time.
4. Before revival, check CPU churn, active agents, and write ownership.
5. Use a resume packet with explicit max runtime, max steps, and validation target.
6. Stop a revived task if it times out twice unchanged, duplicates another agent, or loses its live evidence trail.
7. Promote lessons from revived tasks into skills or scripts so the same task does not break again.

### Revival Model Contract

- Revived old threads default to `gpt-5.5`.
- Use `xhigh` reasoning for stack-wide audits, config changes, timeout forensics, cross-machine propagation, security-sensitive work, or any task with high blast radius.
- Use `high` reasoning for normal repo edits, media-pipeline repair, nontrivial debugging, and task synthesis.
- Use `medium` reasoning for bounded doc updates, inventory, or deterministic validation.
- Use `low` reasoning only for tightly scoped subagent/explorer slices that do not own risky decisions.
- Do not revive an old thread on a stale model profile unless the model choice is explicitly recorded as a deliberate bounded downgrade.

## Context-Budget Necromancy

Use old threads and automation lanes to save main-thread context:

1. Do not paste whole old transcripts into the active lane.
2. Send compact steering packets that point to artifacts, current files, and exact questions.
3. Ask revived threads to return only:
   - confirmed current evidence,
   - changed file paths,
   - blockers,
   - tests/probes run,
   - next concrete action.
4. Prefer artifact pointers over copied content:
   - workstream JSON,
   - task ledgers,
   - crash logs,
   - culprit maps,
   - active queue files,
   - diff-visible patches.
5. If an old thread cannot refresh itself against live evidence, mark its result stale instead of importing it as truth.
6. Keep the main lane's context budget for decisions, integration, and user-visible progress.

## New Capability Audit

When Eddie says a new Codex/model/tool capability is live, audit local capability drift before assuming old limits:

1. Check live Codex config and repo-backed machine profiles for model defaults and reasoning defaults.
2. Check exposed MCP/tool surfaces and local skill inventories.
3. Check whether new subagent roles, model names, or reasoning efforts are available in the current session.
4. Check local hardware lanes and authoritative model planes on that machine.
5. Check docs or official sources only when the capability depends on current vendor behavior.
6. Update stale skills, profiles, or docs that would steer agents back to old limits.
7. Validate candidate-first where config or runtime defaults are fragile.

## File And Log Discipline

- Do not use `rg.exe` on Eddie's machines.
- Do not run broad recursive scans over repo roots, media trees, `.runtime`, model caches, or session archives unless there is a hard cap and a clear exclusion list.
- Prefer known files, recent files, or bounded top-level inventories.
- Use `Get-ChildItem` with `-File`, `-Directory`, `-Filter`, and explicit roots.
- For session logs, prefer `-Tail`, recent-only search, or an index.
- For image/media trees, avoid repeated full-tree hashing; use size, mtime, recent windows, or cached hashes first.

## Common Culprits

Look first for:

- `while ($true)` or `do { } while ($Loop)` without max runtime or max passes.
- `Invoke-RestMethod` or `Invoke-WebRequest` without `-TimeoutSec`.
- Python `subprocess.run` without `timeout=`.
- JavaScript `fetch` without `AbortController`.
- polling loops without backoff or jitter.
- recursive file enumeration followed by full materialization.
- full-tree `Get-FileHash` over large image/model/session roots.
- local-agent queues that keep re-dispatching after the operator lane is already active.

## Required Report Shape

Use Eddie's task-list format for ongoing audits:

```text
X out of Y tasks completed
1. ...
2. ...
ZZ. ALWAYS RECHECK THE OPEN WORK AND LOOK FOR MORE TO DO
```

Reports must separate:

- confirmed current state,
- inferred risk,
- action taken,
- remaining blocker,
- next concrete repair step.

## Loopback

If the lane is still unstable:

1. Re-run a bounded CPU/listener/process sample.
2. Recheck active diffs and subagents.
3. Recheck old-thread steering packets and revived-task status.
4. Patch the next highest-confidence repeat offender.
5. Resume the main quest after validation.
6. Continue until Eddie explicitly stops the lane.
