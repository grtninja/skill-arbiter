# BOUNDARIES.md

## Scope

`skill-arbiter` is a Windows-first NullClaw host security app for local skill governance, curated-source discovery, guarded threat suppression, and self-governance.

## Allowed Lane

- Host-local skill governance for installed skills, built-ins, `.system` skills, overlay candidates, and curated third-party sources.
- Curated-source verification, baseline drift detection, upgrade/reconcile checks, and recent-work prioritization.
- Detection of stale or untracked Python, vendored Python launchers, browser auto-launch abuse, hidden-process launch, typosquats, fake installers, persistence hooks, and hostile tool/resource fan-out.
- Guarded quarantine, disable, and admission decisions for skills and related artifacts.
- Operator-mediated destructive response:
  - process kill
  - installed-skill deletion
  - remediation confirmation
- Self-governance over this repo, its generated artifacts, and its release flow so the app cannot become the threat it is meant to stop.
- Local desktop operator surface plus loopback-only agent API.
- Codex app, VS Code, and GitHub Copilot instruction-surface inventory and drift tracking.
- Loopback-only advisor support for any LM Studio-loaded coding model, with local Qwen preference by default.
- Copy-only public support and security metadata inside the desktop app. The app may surface public URLs but must not auto-open browsers.

## Forbidden Lane

- Direct ownership of runtime inference scheduling, persona execution, or hardware dispatch in STARFRAME/MX3/VRM runtime repos.
- Acting as a general autonomous app orchestrator outside declared host-security flows.
- Silent remote execution, remote bind/listen behavior, or arbitrary browser-driven control flows.
- Secret ingestion into repo-tracked files, public export of host-specific evidence, or publication of usernames/absolute private paths.
- Silent scheduled-task creation, PATH pollution, vendored runtime drops, or undeclared long-running background workers.

## Cross-Repo Boundary

- This repo may inspect, inventory, and score skill-related behavior across repos and hosts through documented checks and curated references.
- This repo may quarantine or deny skill/tool surfaces that target:
  - `<PRIVATE_REPO_A>`
  - `<PRIVATE_REPO_B>`
  - `<PRIVATE_REPO_C>`
  - `<PRIVATE_REPO_D>`
  - `<PRIVATE_REPO_E>`
- This repo must not become the source of truth for runtime execution semantics inside those repos. Runtime repos remain authoritative for their own execution behavior.

## Safety Boundary

- No-stop doctrine and minimum runtime law apply to governed repo work until the requested lane has real validation evidence.
- Continue-facing local-agent surfaces keep visible action-state parity and reasoning visibility for operator review.
- Trusted folders, local-subagent state, and patience runtime window contracts are required public-shape governance terms.


- Skill installs and upgrades are executable trust boundaries, not passive content.
- Default posture is fail-closed.
- Known-bad supply-chain signatures may be auto-blocked immediately.
- Quarantine may be automatic in `guarded_auto` mode.
- Case handling may progress through preserve-evidence, quarantine, strip, request/rebuild or blacklist/remove, vector/source audit, documentation, and rescan, provided destructive steps remain operator-confirmed where required.
- Destructive cleanup always requires operator confirmation.
- The desktop app must open before the local agent starts or attaches.
- Health checks must remain lightweight and must not trigger heavy inventory or scan work on cold start.

## Publication Boundary

- Repo-tracked artifacts are public-shape only.
- Machine-generated docs and JSON must use placeholders for private repo names, usernames, and host-specific absolute paths.
- Raw local evidence, audit traces, destructive-action records, and host-specific details stay in ignored local state only.

## Maximum Effort Policy

- Boundary rules do not justify under-fixing dependents.
- Minimal-diff behavior is forbidden.
- Cross-boundary changes must update all affected runtime, governance, validation, and documentation surfaces together.
