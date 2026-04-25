# AGENTS.md

Repository rules for `skill-arbiter`.

## 1) Core policy

- Treat this repository as public-shape only.
- `skill-arbiter` is now a live NullClaw host security app, not a passive `rg.exe` moderator.
- The shipped product is a local desktop UI plus a loopback-only Python arbitration agent.
- Startup order is mandatory:
  - app open
  - agent attach/start
  - self-checks
  - inventory refresh
  - operator actions enabled
- Desktop launch acceptance is strict:
  - no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows may flash or remain open during startup
  - transient empty-shell flash during startup counts as a failed launch, not a cosmetic issue
  - PowerShell or `cmd` wrapper commands are developer helper paths only, not accepted public desktop launch surfaces
  - canonical no-shell launch surfaces are `scripts/launch_security_console.vbs` and installed shortcuts targeting `wscript.exe`
- Do not launch external browsers as part of normal app behavior.
- Do not silently create scheduled tasks, PATH mutations, hidden workers, or vendored runtime drops.

Required placeholders:

- Repo names: `<PRIVATE_REPO_A>`, `<PRIVATE_REPO_B>`, `<PRIVATE_REPO_C>`, `<PRIVATE_REPO_D>`, `<PRIVATE_REPO_E>`
- Skills root: `$CODEX_HOME/skills`
- User paths: `$env:USERPROFILE\\...`
- External local roots: `<external-candidate-root>`
- Canonical STARFRAME repo root on this workstation: `G:\\GitHub`
- Authoritative model planes for meta-harness work: `http://127.0.0.1:9000/v1` and `http://127.0.0.1:2337/v1`
- Non-authoritative operator surface: `http://127.0.0.1:1234/v1`

## 2) Hard privacy lock

These must pass before commit or release:

```bash
./scripts/install_local_hooks.sh
python3 scripts/check_private_data_policy.py --staged
python3 scripts/check_private_data_policy.py
```

If the gate fails, stop and remove the leak before proceeding.

## 3) Release workflow

For release-impacting changes:

```bash
python3 scripts/prepare_release.py --part patch
```

Then update `CHANGELOG.md` so it matches shipped behavior.

## 4) Validation checklist

Run from repo root:

```bash
python3 scripts/arbitrate_skills.py --help
python3 scripts/nullclaw_agent.py --help
python3 scripts/generate_skill_catalog.py
python3 scripts/check_private_data_policy.py
python3 scripts/check_public_release.py
pytest -q
python3 -m py_compile scripts/arbitrate_skills.py scripts/check_private_data_policy.py scripts/check_public_release.py scripts/generate_skill_catalog.py scripts/nullclaw_agent.py scripts/nullclaw_desktop.py scripts/prepare_release.py scripts/check_release_hygiene.py skill_arbiter/about.py skill_arbiter/meta_harness_policy.py skill_arbiter/public_readiness.py skill_arbiter/self_governance.py
```

## 5) Skill authoring and governance rules

- Keep candidate skills concise and move detailed guidance into `references/`.
- Use the same policy engine for third-party skills and for this repo's self-governance.
- Do not auto-install from unvetted third-party sources.
- Keep built-in VS Code/Codex skills as upstream baseline.
- Reconcile overlay candidates additively; do not disable built-ins to make overlays work.
- Every new or changed skill must remain attributable and privacy-safe.

## 6) Local advisor requirement

- The app must use a dedicated local coding-security LLM.
- Default lane is a fast local Qwen-compatible model exposed through an OpenAI-compatible endpoint.
- Defaults:
  - `NULLCLAW_AGENT_BASE_URL=http://127.0.0.1:9000/v1`
  - `STARFRAME_HOSTED_LARGE_BASE_URL=http://127.0.0.1:2337/v1`
  - `NULLCLAW_AGENT_MODEL=radeon-qwen3.5-4b`
- Candidate skills that encode workstation model authority must treat `:9000` and `:2337` as authoritative, and `:1234` only as a non-authoritative operator surface.
- Candidate skills that encode local repo paths must normalize legacy `Documents\\GitHub` aliases to `G:\\GitHub`.
- Do not point the advisor at remote hosts by default.
- Keep the public repo host-agnostic: the advisor must work with any loopback-hosted OpenAI-compatible coding-model surface, including LM Studio, MemryX shim lanes, and other local model software.
- Do not hard-code one private workstation topology into repo-tracked docs unless it is expressed as a placeholder or compatibility example.

## 7) Documentation lockstep

When policy or workflow changes, update the affected docs in the same change:

- `AGENTS.md`
- `BOUNDARIES.md`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SKILL.md`
- `skill-catalog.md`
- `.github/pull_request_template.md`
- `docs/PROJECT_SCOPE.md`
- `docs/SCOPE_TRACKER.md`
- `references/skill-catalog.md`
- `references/usage-chaining-multitasking.md`
- `references/vscode-skill-handling.md`
- `references/skill-progression.md`
- `references/default-skill-system.md`

## 8) Skill level-up declaration

When a skill is created or materially improved, include:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```

## 9) Maximum effort policy

- Minimal-diff behavior is forbidden.
- Synchronize runtime, docs, tests, release metadata, and generated references together.
- The task is not complete until related governance and dependent repo-facing surfaces are updated.

## Skill-Arbiter Workflow (Binding)

- Skill-arbiter discipline is explicit in this repo: do not take a skill-less turn when an applicable local skill exists.
- Private repo delivery is a hard rule: every Codex change lane must start on a branch, open a PR while work is active, push all repo diffs for that lane, merge back to `main`, sync local `main`, and leave the repo with no uncommitted lane diffs.
- Dirty private repos are not an acceptable stopping point. If a lane inherits an already-dirty worktree, either package the whole current diff into the active PR or record an explicit operator-owned exclusion before claiming completion.
- Route substantial work through `skill-hub` first and state the selected skill order in the work summary.
- For local hardware-, desktop-, or service-backed work, use `local-compute-usage` early and fail closed if the required local lane is unavailable.
- For high-volume, long-running, or agent-heavy work, use `usage-watcher` to choose a bounded operating mode and keep local churn under control.
- When the task has 2 or more independent lanes, use `multitask-orchestrator` and keep merge criteria explicit.
- Use bounded subagents only for sidecar analysis or truly parallel independent lanes; do not leave idle agents open and do not delegate away local ownership.
- The user's selected operating mode is authoritative. Recommendations from `usage-watcher` or `skill-cost-credit-governor` may inform the lane plan, but they must not silently override operator intent.
- Healthy local OpenClaw-compatible subagents are the preferred lane for quick bounded tasks.
- Cloud subagents must default to lower-reasoning, low-cost sidecar work, preserving premium reasoning budget for the main lane.
- Fast mode is not permitted as an automatic escalation path in this repo's governed subagent workflow.
- Substantial governed work should be framed and recorded as quests so each request has a human-readable chain, checkpoints, and a usable end-state, with cumulative agent progression rising from repeated quest completion.
- If the user explicitly names skills, use all named skills in that turn.

## Meta-Harness Parity Contract

- Canonical workstation repo root references use `G:\GitHub`; legacy aliases must be normalized before reporting or acting on repo paths.
- Continue and GitHub Copilot are local-agent continuity surfaces for this project, not browser-first fallbacks.
- LM Studio may appear as a compatible local model host, but authoritative local advisor routing remains explicit and visible.
- Keep every user-visible operator surface honest: backend health is not enough if the operator cannot use the UI or lane.
- Local-agent work must preserve visible action-state parity, reasoning visibility, trusted folders, and local-subagent evidence in summaries and PR notes.
- The no-stop doctrine and minimum runtime law are repository governance terms: do not convert active guidance into a premature wrap-up.
- The patience runtime window applies to long or resumed local-agent work; report evidence quality while continuing concrete repair.
- The mandatory skill chain for ambiguous, resumed, cross-repo, high-volume, or policy-sensitive work includes `skill-hub`, `request-loopback-resume`, `skill-common-sense-engineering`, `usage-watcher`, `skill-cost-credit-governor`, and `skill-trust-ledger`.
