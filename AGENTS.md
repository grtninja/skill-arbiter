# Skill Arbiter — Affirmative Agent Contract

## Product Role

Skill Arbiter is the public-shape Windows-first NullClaw host-security and skill
governance application. It ships a visible desktop console, a loopback-only
arbitration agent, skill and plugin admission, curated-source review, lifecycle
evidence, privacy validation, and public-safe operator documentation.

## High-Effort Completion Contract

- Apply high effort and thorough reasoning from task intake through implementation, verification, documentation, packaging, release preparation, and operator-visible acceptance.
- Optimize for complete, coherent, maintainable delivery across every task-relevant skill, plugin, tool, worker, service, test, registry, generated catalog, document, and integration contract.
- Continue productive work until the requested deliverable is complete or a concrete external dependency is proven with current evidence and an exact continuation path.
- State required behavior directly and affirmatively. Skills, prompts, profiles, model instructions, agent contracts, quest text, and operator guidance name high effort, thorough work, complete delivery, durable verification, and visible acceptance.
- Preserve privacy, provenance, exact lifecycle ownership, operator review, and public-shape compatibility throughout the work.

## Public-Shape And Privacy Contract

- Keep repository-tracked material public-safe and host-agnostic.
- Use placeholders such as `<PRIVATE_REPO_A>`, `<external-candidate-root>`, `<HOST_PROFILE_ID>`, `$CODEX_HOME/skills`, and `$env:USERPROFILE\...` for private topology and paths.
- Keep credentials, raw local evidence, usernames, private absolute paths, personal context, destructive-action records, and private governance in ignored local state or the owning private repository.
- Run privacy and release gates before commit, pull request, or release:

```powershell
python scripts/check_private_data_policy.py --staged
python scripts/check_private_data_policy.py
python scripts/check_public_release.py
```

## NullClaw Desktop Contract

Canonical startup sequence:

1. open the visible desktop application;
2. attach or start the exact owned loopback agent;
3. complete self-checks;
4. refresh inventory and policy state;
5. enable admitted operator actions;
6. maintain current heartbeat and lifecycle evidence.

- Use `scripts/launch_security_console.vbs` and installed shortcuts targeting `wscript.exe` as the public no-shell launch surfaces.
- Keep terminal helpers available for development and diagnosis with explicit ownership and bounded lifecycle.
- Bind browser launch, scheduled-task creation, PATH changes, worker installation, and runtime placement to visible operator actions and durable receipts.
- No-empty-shell acceptance means no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows may flash or remain open during a release-ready launch.
- Keep terminal and background processes intentional, identity-bound, renewable, bounded, and joined.

## Model And Advisor Contract

- Use an operator-selected loopback OpenAI-compatible coding and security model.
- Treat `http://127.0.0.1:9000/v1` as the public authoritative model plane.
- Treat `http://127.0.0.1:2337/v1` as the hosted large-model authoritative lane when explicitly selected.
- Treat `http://127.0.0.1:1234/v1` as a non-authoritative LM Studio operator surface only.
- Treat `http://127.0.0.1:9000` as the MX3 device, DFP, perception, telemetry, and compatibility service boundary.
- Bind model selection to operator intent, current inventory, capability fit, and measured evidence.
- Keep public provider policy compatible with any admitted loopback OpenAI-compatible model host.

## Complete Skill Workflow

- Preserve trusted folders, local-subagent state, reasoning visibility, and the patience runtime window as operator-visible continuity contracts.
- Discover every task-relevant first-party skill before implementation.
- Read each selected `SKILL.md`, declare execution order, and complete its full workflow.
- Use the governed baseline chain when applicable: `skill-hub`, `request-loopback-resume`, `skill-common-sense-engineering`, `usage-watcher`, `skill-cost-credit-governor`, and `skill-trust-ledger`.
- Use `local-compute-usage` for local hardware, desktop, model, and service lanes.
- Use `multitask-orchestrator` for genuinely independent parallel lanes with explicit integration criteria.
- Use bounded subagents while preserving one named owner, task lease, deadline, privacy boundary, and evidence lineage.
- Use every skill the operator explicitly names.

## Skill Authoring And Governance

- Keep each `SKILL.md` concise and place detailed methods, schemas, examples, and evidence in `references/`.
- Use the same policy engine for candidate review and repository self-governance.
- Preserve built-in and `.system` skills as upstream evidence and reconcile local overlays additively.
- Keep every new or changed skill attributable, privacy-safe, testable, capability-specific, and compatible with current tools.
- Include the progression declaration for each created or materially improved skill:

```text
New Skill Unlocked: <SkillName>
<SkillName> Leveled up to <LevelNumber>
```

## Thorough Validation

Run the complete task-relevant set:

```powershell
python scripts/arbitrate_skills.py --help
python scripts/nullclaw_agent.py --help
python scripts/generate_skill_catalog.py
python scripts/check_private_data_policy.py
python scripts/check_public_release.py
pytest -q
$compileFiles = @(
    Get-ChildItem -Path scripts,skill_arbiter -Recurse -File -Filter '*.py' |
        Where-Object { $_.FullName -notmatch '[\\\\/](?:__pycache__|\\.venv)(?:[\\\\/]|$)' } |
        ForEach-Object { $_.FullName }
)
python -m py_compile @compileFiles
git diff --check
```

Add focused regressions for each repaired privacy, authority, lifecycle,
capability, export, and generated-artifact boundary. Pair synthetic process tests
with authorized real Windows lifecycle and desktop acceptance where applicable.

## Documentation Lockstep

Update every materially affected source and generated surface in the same exact
head, including `AGENTS.md`, `INSTRUCTIONS.md`, `BOUNDARIES.md`, `README.md`,
`CONTRIBUTING.md`, `SECURITY.md`, `SKILL.md`, the pull-request template, project
scope, scope tracker, capability documentation, catalogs, aliases, overlays, and
release metadata.

## Affirmative Definition Of Done

Work is complete when the root cause is repaired, every materially affected
skill and product surface is synchronized, current exact-head verification is
captured, privacy and release gates pass, lifecycle ownership is proven, the
requested visible workflow succeeds, and every concrete external dependency has
a precise continuation path.
