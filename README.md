# skill-arbiter

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.txt)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform: Windows-focused](https://img.shields.io/badge/platform-Windows--focused-informational)

`skill-arbiter` is a Windows-first NullClaw host security app for local skill governance, curated-source discovery, guarded threat suppression, and self-governance.

It started as an `rg.exe` churn moderator. It now acts as a capability firewall for local agent skills and related automation surfaces.

Local skill governance and threat suppression console with guarded operator actions, source legitimacy tracking, and operator-confirmed remediation.

## For humans

Use this repository as the public-shape Skill Arbiter project: a defensive local-host console for reviewing skills, process policy, release readiness, and operator-mediated remediation. Keep private workstation paths, raw host evidence, and sealed local stack details out of repo-tracked artifacts.

## For AI agents

Use the repo-owned validation gates before claiming readiness. Applicable local skills remain mandatory, the local-agent contract stays visible in work summaries, and private repo work must end through a PR that is pushed, merged into `main`, synced locally, and left clean.

## Shared Governance Baseline

This repo stays aligned to the public-safe governance baseline in
`BOUNDARIES.md`, `docs/PROJECT_SCOPE.md`, `docs/SCOPE_TRACKER.md`, and the
generated alignment references shipped in `references/`.

## Discovery index

Use [`skill-catalog.md`](skill-catalog.md) as the canonical repo-owned skill
index for humans, mirrors, and crawlers. The generated
[`references/skill-catalog.md`](references/skill-catalog.md) remains the deeper
inventory and governance view.

## App preview

Public-safe preview capture from an isolated browser session:

![Skill Arbiter Security Console preview](docs/images/skill-arbiter-security-console-public-preview.png)

## Reality check

The desktop app is not a fully self-sufficient operator product yet.

- Standalone desktop use still covers local inventory, baseline reconciliation, attribution, and mitigation.
- The app is only fully meaningful when real work is being driven through Codex or GitHub Copilot instruction surfaces.
- Without active Codex/Copilot-driven work, the interop view, collaboration lane, skill-game lane, and upgrade/consolidation recommendations stay part of the harness but can become sparse, stale, or much less useful.
- Do not describe the current app as a complete general-purpose skill-security console outside Codex/Copilot-driven workflows.

## OpenJarvis Wave 1 role

In the private OpenJarvis-style rollout, `skill-arbiter` is the bounded
governance and learning engine.

It may schedule, critique, archive, and tune within declared limits, but it may
not silently promote accepted baselines or perform destructive cleanup without
operator confirmation.

## Response governance alignment

`skill-arbiter` participates in the shared response loop as a bounded
governance layer:

1. candidate generation
2. decision telemetry
3. ranked arbitration
4. trace recording
5. final emission

In that loop, this repo may:

- critique candidates
- gate risky or out-of-policy candidates
- recommend tuning or retries
- record trust and reliability outcomes

It may not:

- invent a second persona authority
- silently emit final answers on behalf of endpoint repos
- bypass trace requirements because a candidate "looks good enough"

## AI warning

- Codex, GitHub Copilot, and other AI/agent systems can make mistakes.
- This app can surface useful governance and risk signals, but it does not turn AI output into ground truth.
- Operator review is still required before trusting destructive actions, provenance claims, upgrade advice, or security conclusions.
- If the app, agent, or upstream AI workflow disagrees with observed reality, treat that as a bug or mismatch to investigate, not proof that the machine is right.

## What it does

- Inventories installed skills under `$CODEX_HOME/skills`
- Reconciles built-in VS Code/Codex skills against the official `openai/skills` baseline
- Tracks `.system` skills, overlay candidates, curated third-party sources, and recent-work-relevant skills
- Scores high-risk patterns:
  - typosquats and fake installers
  - npm/npx/postinstall persistence
  - stale and untracked Python
  - vendored `python.exe` / `pythonw.exe`
  - hidden process launch
  - browser auto-launch abuse
  - credential prompt theft patterns
  - broad process-kill logic
  - tool/resource fan-out with remote execution surfaces
- Applies guarded local response:
  - admit
  - quarantine
  - disable
  - operator-confirmed delete / kill
- Audits itself with the same policy engine so the app does not become part of the problem
- Records collaboration outcomes and recommends governed skill creation, upgrades, or consolidation from real agent work
- Records quests as human-readable request-to-result paths with steps, checkpoints, deliverables, evidence, and cumulative agent progression

## Runtime model

- Desktop shell: embedded local UI via `pywebview`
- Agent: loopback-only Python server on `127.0.0.1:17665`
- Default policy mode: `guarded_auto`
- UI model: layered operator workflow with critical-first triage
- Loopback API state responses are served `no-store` so the embedded desktop cannot silently reuse stale inventory, skill-game, or collaboration data
- Full-value mode depends on active Codex or GitHub Copilot work feeding instruction-surface, collaboration, and skill-learning evidence
- Quest mode treats substantial governed work as a request -> chain -> checkpoint -> outcome path; quest completion feeds both per-skill quest XP and cumulative agent XP so a higher-level agent is the result of repeated successful governed runs
- Startup flow:
  1. app open
  2. agent attach/start
  3. self-checks
  4. inventory refresh
  5. operator actions enabled
- Desktop launch acceptance is strict:
  - no empty `cmd.exe`, `powershell.exe`, or `pwsh.exe` windows may flash or remain open during startup
  - public desktop launch surfaces must stay shell-free; PowerShell or `cmd` wrappers are developer helpers only
- No external browser launch in the normal operator path

## Local advisor

The app uses a dedicated local coding-security advisor for short notes and live
runtime supervision.

Defaults:

- `NULLCLAW_AGENT_BASE_URL=http://127.0.0.1:9000/v1`
- `STARFRAME_HOSTED_LARGE_BASE_URL=http://127.0.0.1:2337/v1`
- `NULLCLAW_AGENT_MODEL=radeon-qwen3.5-4b`
- `NULLCLAW_AGENT_ENABLE_LLM=1`

The advisor must remain loopback-local by default.

Compatibility contract:

- The advisor may use any loopback-hosted OpenAI-compatible coding-model surface.
- Supported local hosts include LM Studio, MemryX shim lanes, and other local model services exposing `/v1/models` and `/v1/chat/completions`.
- On the maintainer workstation, `http://127.0.0.1:9000/v1` is the public authoritative plane and `http://127.0.0.1:2337/v1` is the hosted 27B authoritative lane.
- `http://127.0.0.1:1234/v1` remains a non-authoritative operator surface and should not be treated as the source of routing truth.
- The runtime now probes multiple local loopback endpoints and follows the first live compatible lane instead of assuming one fixed model host forever.
- No remote advisor host is allowed by default.

Model policy:

- Fast local Qwen-compatible lanes are preferred for the default operator path.
- Operator overrides are allowed for narrow specialized tasks, but they must remain local, explicit, and visible in the app state.
- Repo-tracked docs must describe model compatibility generically rather than hard-coding one private workstation layout.

Subagent routing policy:

- The user's selected mode remains authoritative.
- Healthy local OpenClaw-compatible subagents are preferred for quick bounded work.
- Cloud subagents are treated as part of the same governed pool, but default to lower-reasoning, lower-cost sidecar work.
- Fast mode is not part of the governed default path.

## Quick start

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Install desktop shell dependencies (required for the managed security-console launcher):

```bash
cd apps/nullclaw-desktop
npm install
```

Open the desktop app for developer/debug work:

```bash
python scripts/nullclaw_desktop.py
```

The Python entrypoint is not the accepted public desktop launch surface because it can still inherit a visible shell host.

Open the desktop app through the accepted no-shell Windows launcher:

```powershell
wscript.exe //B //Nologo .\scripts\launch_security_console.vbs
```

Developer helper from an already-open shell:

```powershell
.\scripts\start_security_console.ps1
```

The managed launcher expects a repo-local Electron runtime under `apps/nullclaw-desktop/node_modules/electron`.
Do not treat the PowerShell helper as a public desktop startup path; the accepted no-flash launch surfaces are the VBS launcher and the installed shortcuts.

Install branded desktop and Start Menu shortcuts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_security_console_shortcut.ps1
```

The installed shortcuts use a silent `wscript` launcher so the console does not bounce through visible PowerShell or `cmd` wrappers, and startup acceptance is not met if an empty shell window flashes even briefly.

Stop the desktop app and loopback agent cleanly:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_security_console.ps1
```

Run the agent headless:

```bash
python scripts/nullclaw_agent.py
```

Refresh the machine-generated catalog:

```bash
python scripts/generate_skill_catalog.py
```

Run the privacy gate:

```bash
python scripts/check_private_data_policy.py
```

Refresh the machine-generated vetting report:

```bash
python scripts/generate_skill_vetting_report.py
```

Refresh the machine-generated SkillHub alignment artifacts:

```bash
python scripts/generate_skillhub_alignment.py
```

Run the secret hygiene gate:

```bash
python scripts/check_secret_hygiene.py
```

Run the external review hygiene gate:

```bash
python scripts/check_external_review_hygiene.py
```

Run the public-release gate:

```bash
python scripts/check_public_release.py
```

## GitHub Actions policy

This public repo is configured for a `local_only` GitHub Actions policy.

- CI and secret-scan workflows must remain self-contained and repo-local.
- Do not add marketplace or third-party `uses:` steps unless the repository
  policy changes first.
- Workflow startup should rely on shell steps plus in-repo Python checks so the
  public branch still validates under restricted Actions settings.

## Skill doc review policy

`skill-candidates/**/SKILL.md` and their adjacent references are treated as
behavior-governing surfaces.

- Review them like prompt-policy or orchestration code, not passive prose.
- Human review is required for changes to trigger language, scope boundaries,
  loopback/escalation/approval semantics, and examples that imply runtime or
  host assumptions.
- External contributor PRs should not add workflow hooks, vendor review
  integrations, or secret-bearing config changes unless explicitly requested by
  a maintainer.
- Repo-local automation enforces an external review hygiene gate over governed
  surfaces to catch vendor-review markers and non-local workflow actions before
  merge.

## Local API

The desktop UI talks to a local-only loopback API:

- `GET /v1/health`
- `GET /v1/quests/status`
- `POST /v1/quests/record`
- `GET /v1/about`
- `POST /v1/self-checks/run`
- `GET /v1/privacy/status`
- `POST /v1/inventory/refresh`
- `GET /v1/inventory/skills`
- `GET /v1/inventory/sources`
- `GET /v1/incidents`
- `GET /v1/mitigation/cases`
- `POST /v1/mitigation/plan`
- `POST /v1/mitigation/execute`
- `GET /v1/collaboration/status`
- `POST /v1/collaboration/record`
- `GET /v1/skill-game/status`
- `POST /v1/skill-game/record`
- `GET /v1/public-readiness`
- `POST /v1/public-readiness/run`
- `GET /v1/agent-runtime/status`
- `POST /v1/admission/evaluate`
- `POST /v1/quarantine/apply`
- `POST /v1/actions/confirm`
- `GET /v1/audit-log`

## Inventory coverage

The live inventory pipeline covers:

- installed top-level skills
- installed `.system` skills
- overlay candidates under `skill-candidates/`
- official OpenAI upstream baseline from `openai/skills`
- local Codex config under `%USERPROFILE%\\.codex`
- Codex app, VS Code, and GitHub Copilot instruction surfaces across the local workspace
- curated third-party sources already tracked by the repo
- threat-matrix references for OpenClaw / NullClaw discovery surfaces
- recent-work relevance from cross-repo radar artifacts
- ownership and legitimacy scoring for official built-ins, repo-owned skills, candidates, and unowned local installs
- rejected third-party candidate stubs stay attributable in the repo references, but are kept out of the active live inventory until they are rebuilt or explicitly installed for review

What this does **not** mean:

- the desktop alone can infer meaningful collaboration history without Codex/Copilot-driven work
- the skill-game lane can stay present as part of the harness, but progression quality depends on real governed agent work being recorded
- the interop surfaces prove much on their own beyond presence-level tracking unless Codex/Copilot workflows are actually active

See:

- [references/skill-catalog.md](references/skill-catalog.md)
- [references/skill-vetting-report.md](references/skill-vetting-report.md)
- [references/OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md](references/OPENCLAW_NULLCLAW_THREAT_MATRIX_2026-03-11.md)
- [references/vscode-skill-handling.md](references/vscode-skill-handling.md)
- [references/skillhub-alignment-matrix.md](references/skillhub-alignment-matrix.md)
- [references/skillhub-source-ledger.md](references/skillhub-source-ledger.md)

## Collaboration and skill learning

The console now records governed collaboration outcomes from real agent work and turns repeatable
patterns into actionable skill recommendations.

- These lanes are part of the harness in this app. Real Codex or GitHub Copilot-driven work improves their evidence quality; without that input, the app still opens and inventories locally but progression and recommendations become thinner.
- collaboration events are stored in local-only state
- trust-ledger and skill-game lanes receive the same outcome evidence
- the skill-game now reports the original long-lived skill levels from `references/skill-progression.md`
- those original levels are a longitudinal progress ledger for the real skill estate, not a deprecated legacy-only display
- the desktop app can recommend whether a pattern should become a new skill, an upgrade, or a consolidation
- `heterogeneous-stack-validation` is the governed candidate lane for mixed local-plus-remote validation work like the current stack sweep
- The desktop shows section-local refresh failures in place instead of leaving zero/default placeholders that can look like data loss

## Usage reduction and local compute evidence

The cost and routing skills now consume loopback stack accounting evidence rather
than reasoning only from manual credit logs or static budgets.

- `usage-watcher`
- `local-compute-usage`
- `skill-cost-credit-governor`

These skills can now ingest and compare:

- `TPK`
- `authoritative_cost`
- `displacement_value_preview`
- `benchmark_api_equivalent_cost`
- `local_marginal`
- `cloud_equivalent`
- `savings vs cloud`
- routing/provider provenance
- local runtime latency and lane health

The key contract is dual-ledger:

- `authoritative_cost` remains strict billing truth
- `displacement_value_preview` remains benchmarked non-billing shadow value

That distinction is now a governed input to usage reduction, local-first routing,
and skill upgrade recommendations instead of a manual after-the-fact story.

Empirical mode selection is also a governed input now.

See:

- [references/empirical-mode-routing-telemetry.md](references/empirical-mode-routing-telemetry.md)
- [references/usage-mode-session-template.json](references/usage-mode-session-template.json)

Use these when a real usage pattern shows that:

- greenfield app work behaves differently from maintenance,
- lower-cost sessions can still outperform high-burn sessions on steady progress,
- completion-adjusted progress is a better policy signal than raw spend alone.

The same telemetry also governs subagent placement:

- local OpenClaw-compatible subagents first
- lower-reasoning cloud sidecars second
- premium reasoning preserved for the main lane unless the operator explicitly escalates

## Mitigation workflow

The desktop app treats findings as live mitigation cases, not static warnings.

Operator flow inside the desktop app:

1. startup flow and host/agent state
2. critical queue with critical and high findings pinned at the top
3. active finding explainer and runbook
4. mitigation actions
5. inventory, sources, and interop review
6. privacy, release, support, and audit evidence

Default response chain:

1. preserve evidence
2. quarantine fast
3. strip suspicious artifacts
4. report the case
5. request review if the skill looks legitimate
6. rebuild clean from a trusted source when possible
7. blacklist if hostile
8. remove or refactor
9. audit threat vectors
10. audit sources
11. evaluate adjacent vectors
12. document the outcome
13. repeat the scan

Case planning now separates:

- `official_trusted`
- `owned_trusted`
- `needs_review`
- `blocked_hostile`

so the console can legitimize the local stack without pretending every dangerous capability is malware.

## Public-shape rule

This repository is public-shape only.

- Do not commit usernames, personal names, absolute private paths, private repo names, raw host evidence, or secrets unless explicitly authorized for public release.
- Repo-tracked docs and JSON stay placeholder-safe.
- Raw local evidence, audit events, and destructive-action records stay in ignored local state.

## SkillHub alignment

`skill-arbiter` now treats SkillHub as a bounded discovery surface, not a
trusted install source by default.

- SkillHub metadata may be used for shortlist building and gap mapping.
- Candidate content must still be resolved back to GitHub and pass third-party intake plus lockdown admission before import.
- The current source posture is recorded in `references/skillhub-source-ledger.*`.
- SkillHub is only promotable above `discovery_only` after a clean bounded first wave.

## Public support

Public support and project links surfaced by the desktop app:

- GitHub repo: `https://github.com/grtninja/skill-arbiter`
- GitHub issues: `https://github.com/grtninja/skill-arbiter/issues`
- GitHub security: `https://github.com/grtninja/skill-arbiter/security`
- Patreon: `https://www.patreon.com/cw/grtninja`

The desktop UI copies these links to the clipboard instead of opening external browsers automatically.

See also:

- [SUPPORT.md](SUPPORT.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Public release readiness

Before publishing or widening distribution:

1. Run `python scripts/check_private_data_policy.py`.
2. Run `python scripts/check_public_release.py`.
3. Confirm the desktop app shows a passing Public Release panel.
4. Confirm icon assets and shortcut installers are present.
5. Confirm repo-tracked files remain public-shape only.

## Safety and abuse handling

`skill-arbiter` is a defensive local-host security console.

- It is for quarantine, review, and remediation of risky skills and automation surfaces.
- It is not for persistence abuse, credential theft, remote compromise, or stealth operator bypass.
- Destructive actions stay operator-mediated or clearly audited in local-only state.
- Public docs and artifacts stay sanitized so the repository does not become a leak surface.

## Validation

```bash
python scripts/arbitrate_skills.py --help
python scripts/nullclaw_agent.py --help
python scripts/generate_skill_catalog.py
python scripts/generate_skill_vetting_report.py
python scripts/generate_skillhub_alignment.py
python scripts/check_private_data_policy.py
python scripts/check_external_review_hygiene.py
python scripts/check_secret_hygiene.py
python scripts/check_public_release.py
pytest -q
python -m py_compile scripts/arbitrate_skills.py scripts/check_private_data_policy.py scripts/check_external_review_hygiene.py scripts/check_secret_hygiene.py scripts/check_public_release.py scripts/generate_skill_catalog.py scripts/generate_skill_vetting_report.py scripts/nullclaw_agent.py scripts/nullclaw_desktop.py skill_arbiter\\about.py skill_arbiter\\agent_server.py skill_arbiter\\external_review_hygiene.py skill_arbiter\\inventory.py skill_arbiter\\llm_advisor.py skill_arbiter\\meta_harness_policy.py skill_arbiter\\mitigation.py skill_arbiter\\privacy_policy.py skill_arbiter\\public_readiness.py skill_arbiter\\secret_hygiene.py skill_arbiter\\self_governance.py skill_arbiter\\threat_catalog.py
```

## Repository layout

- `skill_arbiter/`: runtime package for the local NullClaw agent
- `apps/nullclaw-desktop/ui/`: embedded desktop UI
- `scripts/`: entrypoints, generators, and governance utilities
- `skill-candidates/`: overlay skills and candidate skills
- `references/`: generated catalog plus policy/reference material
- `tests/`: regression coverage
- `docs/`: project scope and tracker

## Related docs

- [BOUNDARIES.md](BOUNDARIES.md)
- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SKILL.md](SKILL.md)
- [docs/PROJECT_SCOPE.md](docs/PROJECT_SCOPE.md)
- [docs/SCOPE_TRACKER.md](docs/SCOPE_TRACKER.md)
