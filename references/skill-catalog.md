# Complete Skill Catalog

This document is the canonical skill inventory for this repository's overlay model.

Compatibility policy:
- VS Code/Codex built-in skills are upstream and untouched.
- This repository adds and moderates an overlay set under `skill-candidates/`.
- No workflow here disables or conflicts with VS Code built-ins.

## Inventory Summary

- VS Code built-ins (top-level): 31
- VS Code system built-ins (`.system`): 2
- Repository overlay candidates (`skill-candidates/`): 50
- Total installed skills expected after overlay restore: 83

## VS Code Built-ins (Top-Level)

| Skill | Purpose |
| --- | --- |
| `cloudflare-deploy` | Deploy applications and infrastructure to Cloudflare using Workers, Pages, and related platform services. Use when the user asks to deploy, host, publish, or set up a project on Cloudflare. |
| `develop-web-game` | Use when Codex is building or iterating on a web game (HTML/JS) and needs a reliable development + testing loop: implement small changes, run a Playwright-based test script with short input bursts and intentional pauses, inspect screenshots/text, and review console errors with render_game_to_text. |
| `doc` | Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks. |
| `figma` | Use the Figma MCP server to fetch design context, screenshots, variables, and assets from Figma, and to translate Figma nodes into production code. Trigger when a task involves Figma URLs, node IDs, design-to-code implementation, or Figma MCP setup and troubleshooting. |
| `figma-implement-design` | Translate Figma nodes into production-ready code with 1:1 visual fidelity using the Figma MCP workflow (design context, screenshots, assets, and project-convention translation). Trigger when the user provides Figma URLs or node IDs, or asks to implement designs or components that must match Figma specs. Requires a working Figma MCP server connection. |
| `gh-address-comments` | Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in. |
| `gh-fix-ci` | Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize failure context, draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL. |
| `imagegen` | Use when the user asks to generate or edit images via the OpenAI Image API (for example: generate image, edit/inpaint/mask, background removal or replacement, transparent background, product shots, concept art, covers, or batch variants); run the bundled CLI (`scripts/image_gen.py`) and require `OPENAI_API_KEY` for live calls. |
| `jupyter-notebook` | Use when the user asks to create, scaffold, or edit Jupyter notebooks (`.ipynb`) for experiments, explorations, or tutorials; prefer the bundled templates and run the helper script `new_notebook.py` to generate a clean starting notebook. |
| `linear` | Manage issues, projects & team workflows in Linear. Use when the user wants to read, create or updates tickets in Linear. |
| `netlify-deploy` | Deploy web projects to Netlify using the Netlify CLI (`npx netlify`). Use when the user asks to deploy, host, publish, or link a site/repo on Netlify, including preview and production deploys. |
| `notion-knowledge-capture` | Capture conversations and decisions into structured Notion pages; use when turning chats/notes into wiki entries, how-tos, decisions, or FAQs with proper linking. |
| `notion-meeting-intelligence` | Prepare meeting materials with Notion context and Codex research; use when gathering context, drafting agendas/pre-reads, and tailoring materials to attendees. |
| `notion-research-documentation` | Research across Notion and synthesize into structured documentation; use when gathering info from multiple Notion sources to produce briefs, comparisons, or reports with citations. |
| `notion-spec-to-implementation` | Turn Notion specs into implementation plans, tasks, and progress tracking; use when implementing PRDs/feature specs and creating Notion plans + tasks from them. |
| `openai-docs` | Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations (for example: Codex, Responses API, Chat Completions, Apps SDK, Agents SDK, Realtime, model capabilities or limits); prioritize OpenAI docs MCP tools and restrict any fallback browsing to official OpenAI domains. |
| `pdf` | Use when tasks involve reading, creating, or reviewing PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, and `pypdf` for generation and extraction. |
| `playwright` | Use when the task requires automating a real browser from the terminal (navigation, form filling, snapshots, screenshots, data extraction, UI-flow debugging) via `playwright-cli` or the bundled wrapper script. |
| `render-deploy` | Deploy applications to Render by analyzing codebases, generating render.yaml Blueprints, and providing Dashboard deeplinks. Use when the user wants to deploy, host, publish, or set up their application on Render's cloud platform. |
| `screenshot` | Use when the user explicitly asks for a desktop or system screenshot (full screen, specific app or window, or a pixel region), or when tool-specific capture capabilities are unavailable and an OS-level capture is needed. |
| `security-best-practices` | Perform language and framework specific security best-practice reviews and suggest improvements. Trigger only when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (python, javascript/typescript, go). Do not trigger for general code review, debugging, or non-security tasks. |
| `security-ownership-map` | Analyze git repositories to build a security ownership topology (people-to-file), compute bus factor and sensitive-code ownership, and export CSV/JSON for graph databases and visualization. Trigger only when the user explicitly wants a security-oriented ownership or bus-factor analysis grounded in git history (for example: orphaned sensitive code, security maintainers, CODEOWNERS reality checks for risk, sensitive hotspots, or ownership clusters). Do not trigger for general maintainer lists or non-security ownership questions. |
| `security-threat-model` | Repository-grounded threat modeling that enumerates trust boundaries, assets, attacker capabilities, abuse paths, and mitigations, and writes a concise Markdown threat model. Trigger only when the user explicitly asks to threat model a codebase or path, enumerate threats/abuse paths, or perform AppSec threat modeling. Do not trigger for general architecture summaries, code review, or non-security design work. |
| `sentry` | Use when the user asks to inspect Sentry issues or events, summarize recent production errors, or pull basic Sentry health data via the Sentry API; perform read-only queries with the bundled script and require `SENTRY_AUTH_TOKEN`. |
| `skill-arbiter` | Public candidate skill for arbitrating Codex skill installs on Windows hosts. Use when you need to reintroduce skills one-by-one, detect which skill triggers persistent rg.exe/CPU churn, and automatically remove or blacklist offending skills with reproducible evidence. |
| `sora` | Use when the user asks to generate, remix, poll, list, download, or delete Sora videos via OpenAI\u2019s video API using the bundled CLI (`scripts/sora.py`), including requests like \u201cgenerate AI video,\u201d \u201cSora,\u201d \u201cvideo remix,\u201d \u201cdownload video/thumbnail/spritesheet,\u201d and batch video generation; requires `OPENAI_API_KEY` and Sora API access. |
| `speech` | Use when the user asks for text-to-speech narration or voiceover, accessibility reads, audio prompts, or batch speech generation via the OpenAI Audio API; run the bundled CLI (`scripts/text_to_speech.py`) with built-in voices and require `OPENAI_API_KEY` for live calls. Custom voice creation is out of scope. |
| `spreadsheet` | Use when tasks involve creating, editing, analyzing, or formatting spreadsheets (`.xlsx`, `.csv`, `.tsv`) using Python (`openpyxl`, `pandas`), especially when formulas, references, and formatting need to be preserved and verified. |
| `transcribe` | Transcribe audio files to text with optional diarization and known-speaker hints. Use when a user asks to transcribe speech from audio/video, extract text from recordings, or label speakers in interviews or meetings. |
| `vercel-deploy` | Deploy applications and websites to Vercel. Use when the user requests deployment actions like "deploy my app", "deploy and give me the link", "push this live", or "create a preview deployment". |
| `yeet` | Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`). |

## VS Code Built-ins (`.system`)

| Skill | Purpose |
| --- | --- |
| `skill-creator` | Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. |
| `skill-installer` | Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). |

## Repository Overlay Candidates

### Cross-Repo Utility

| Skill | Purpose |
| --- | --- |
| `code-gap-sweeping` | Sweep one or more local repositories for implementation gaps and produce deterministic, evidence-backed remediation lanes. Use when you need cross-repo detection of missing tests, docs lockstep drift, risky TODO/FIXME additions, and release-hygiene misses. |
| `docs-alignment-lock` | Keep repository policy docs aligned and privacy-safe before PRs. Use when changing workflow/policy text across AGENTS.md, README.md, CONTRIBUTING.md, SKILL.md, PR templates, or skill candidate docs. |
| `local-compute-usage` | Enforce local-first Codex execution through VS Code workspace and connected local apps/services/hardware, with MemryX shim priority and fail-closed remote-host checks. |
| `playwright-edge-preference` | Run Playwright browser automation with Microsoft Edge as the default channel. Use when users request Edge-specific validation, screenshots, or parity checks while keeping deterministic low-churn automation flow. |
| `playwright-safe` | Run browser automation with Playwright using a no-assets, low-churn workflow. Use when you need navigation, form actions, extraction, or screenshots without installing icon/image assets that can trigger repeated rg.exe scans. |
| `request-loopback-resume` | Resume previously requested work deterministically after interruptions. Use when context switches, AFK gaps, or multi-lane pauses require checkpointed state, explicit next actions, and fail-closed resume validation. |
| `safe-mass-index-core` | Build and query bounded metadata-only repository indexes without rg process churn. Use when working in very large repos and you need deterministic file discovery by path, extension, language, scope, or freshness. |
| `usage-watcher` | Reduce paid credit spend and rate-limit risk with deterministic usage analysis and budget guardrails. Use when planning high-volume agent work, reviewing recent burn, or setting lean/standard/surge operating caps. |

### Repo A

| Skill | Purpose |
| --- | --- |
| `repo-a-coordinator-smoke` | Run and debug Repo A DDC node/coordinator smoke workflows. Use when changing coordinator endpoints, job fetch/submit flow, runtime registration, or backend dispatch paths that must be verified with local coordinator execution. |
| `repo-a-policy-selftest-gate` | Enforce Repo A DDC policy and acceptance gates before PRs. Use when changing policy files, node runtime behavior, guardrail-sensitive config, or validation tooling that must satisfy AGENTS.md acceptance commands. |
| `repo-a-telemetry-kv-guard` | Protect Repo A DDC telemetry/privacy and encrypted KV pager contracts. Use when editing repo_c_trace adapters, Repo C policy gate logic, KV tiering/crypto code, or retention/privacy behavior tied to role acceptance. |

### Repo B

| Skill | Purpose |
| --- | --- |
| `repo-b-agent-bridge-safety` | Operate and secure the Continue Agent Bridge in <PRIVATE_REPO_B>. Use when configuring bridge modes, validating /api/agent endpoints, enforcing controlled-write safety gates, or diagnosing bridge availability and permission failures. |
| `repo-b-avatarcore-ops` | Run and validate <PRIVATE_REPO_B> AvatarCore proxy, provider routing, and Unreal bridge lifecycle surfaces. |
| `repo-b-comfy-amuse-capcut-pipeline` | Operate profile-driven ComfyUI pipelines with optional AMUSE enhancement and CapCut export guidance in <PRIVATE_REPO_B>. Use when validating /api/comfy/pipelines/*, /api/amuse/*, or CapCut handoff metadata. |
| `repo-b-control-center-ops` | Operate and debug <PRIVATE_REPO_B> Control Center and thin-waist service surfaces. Use when working on connector routing, Lighthouse checks, MCP/Agent Bridge endpoints, pose bridge, desktop startup/restart behavior, or window lifecycle ownership. |
| `repo-b-hardware-first` | Enforce hardware-first diagnosis and fixes in <PRIVATE_REPO_B>. Use for runtime probe, telemetry, inference, and integration failures where strict real-hardware behavior, no new stubs, deterministic diagnostics, and no unrequested driver/runtime mutation are required. |
| `repo-b-local-bridge-orchestrator` | Run credit-first local Agent Bridge orchestration in <PRIVATE_REPO_B> with strict read-only validation, bounded indexing, and fail-closed guidance hints. Excludes MCP Comfy diagnostics. |
| `repo-b-local-comfy-orchestrator` | Compatibility wrapper for legacy local Comfy orchestration requests in <PRIVATE_REPO_B>. Route new MCP/Comfy operations to repo-b-mcp-comfy-bridge. |
| `repo-b-mass-index-ops` | Run fast non-sharded mass-index operations for <PRIVATE_REPO_B> service lanes. Use when triaging bridge wiring, thin-waist routes, control-center connectors, and runtime helper scripts where quick endpoint-path discovery is required. |
| `repo-b-mcp-comfy-bridge` | Canonical MCP adapter and Comfy bridge operations for <PRIVATE_REPO_B>. Use when enabling MCP, validating shim.comfy resources/tools, operating workflow/pipeline submissions, or running fail-closed Comfy diagnostics with optional AMUSE and CapCut contract checks. |
| `repo-b-preflight-doc-sync` | Enforce <PRIVATE_REPO_B> preflight gates and documentation lockstep. Use before PRs to run required validation profiles and keep README.md, docs/PROJECT_SCOPE.md, and docs/SCOPE_TRACKER.md synchronized with shipped behavior. |
| `repo-b-starframe-ops` | Validate <PRIVATE_REPO_B> STARFRAME API, AvatarCore proxy, persona registry, heartbeat contract, and degraded-mode guardrails. |
| `repo-b-thin-waist-routing` | Validate and troubleshoot thin-waist REST routing in <PRIVATE_REPO_B>. Use when changing /v1 models/chat/vision routes, async job queue endpoints, connector routing policy, or bind/exposure behavior. |
| `repo-b-wsl-hybrid-ops` | Operate and diagnose the Windows-host plus WSL-auxiliary split for <PRIVATE_REPO_B>. Use when validating hybrid service reachability, enforcing hardware-on-Windows boundaries, or debugging cross-host connectivity for ComfyUI and LM Studio helpers. |

### Repo C

| Skill | Purpose |
| --- | --- |
| `repo-c-boundary-governance` | Keep <PRIVATE_REPO_C> changes aligned with BOUNDARIES.md and AGENTS.md governance. Use when modifying trust-layer architecture, cross-repo interfaces, packaging docs, or any change that could blur cognitive vs hardware execution boundaries. |
| `repo-c-mass-index-ops` | Run shard-first mass-index operations for <PRIVATE_REPO_C> governance lanes. Use when scanning policy schemas, ranking/trace contracts, and trust-layer boundaries in very large trees where scope partitioning is required. |
| `repo-c-persona-registry-maintenance` | Maintain persona pack discovery and manifest-driven stack loading in <PRIVATE_REPO_C>. Use when adding/updating persona packs, editing manifest.persona.json files, or changing registry loader behavior in repo_c/persona_registry.py. |
| `repo-c-policy-schema-gate` | Validate Repo C policy files and schema contracts in <PRIVATE_REPO_C>. Use when editing policy manifests, schema files, policy validation CLI logic, or tests that rely on schema conformance. |
| `repo-c-ranking-contracts` | Maintain ranking engine behavior and schema compatibility in <PRIVATE_REPO_C>. Use when modifying scoring weights, ranking/multiplier logic, report serialization, or `ranking_report` schema contracts consumed by downstream systems. |
| `repo-c-shim-contract-checks` | Enforce REPO_B shim runtime contract expectations in <PRIVATE_REPO_C>. Use when changing shim-facing adapters, telemetry dependencies, integration tests, or fail-closed behavior tied to REPO_B_SIDECAR_URL and mock-shim fixtures. |
| `repo-c-trace-ndjson-validate` | Validate Repo C/repo_c_trace NDJSON packet integrity in <PRIVATE_REPO_C>. Use when changing trace packet fields, guardian reroute behavior, or validation tooling that checks packet monotonicity and required envelope keys. |

### Repo D

| Skill | Purpose |
| --- | --- |
| `repo-d-local-packaging` | Run Windows-local packaging and release validation for <PRIVATE_REPO_D>. Use when building distributables, fixing packaging regressions, or validating installer/portable outputs without introducing CI workflows. |
| `repo-d-mass-index-ops` | Run UI-and-packaging mass-index operations for <PRIVATE_REPO_D> workspace trees. Use when scanning renderer components, Electron startup files, workspace packages, and packaging scripts while aggressively excluding generated build artifacts. |
| `repo-d-setup-diagnostics` | Diagnose <PRIVATE_REPO_D> setup wizard and runtime state issues. Use when debugging LM Studio/Kokoro/Lovense setup paths, renderer hydration, profile persistence, or overlay/background behavior. |
| `repo-d-ui-guardrails` | Enforce <PRIVATE_REPO_D> AGENTS.md guardrails for UI/Electron work. Use when modifying apps/desktop, packages/ui, packages/engine, packages/services, or docs tied to deterministic visuals, no-download policy, local-only behavior, and no-CI constraints. |

### Governance and Optimization

| Skill | Purpose |
| --- | --- |
| `skill-arbiter-churn-forensics` | Investigate rg.exe churn and quarantine decisions in skill-arbiter runs. Use when a skill causes CPU spikes, unexpected scans, blacklist actions, or when arbitration thresholds need evidence-backed tuning. |
| `skill-arbiter-lockdown-admission` | Install and admit-test local skills with strict personal policy in the skill-arbiter repo. Use when adding or updating personal skills, requiring local-only sources, pre-admission artifact cleanup, immutable pinning, blacklist quarantine, and rg.exe churn evidence. |
| `skill-arbiter-release-ops` | Run release bump and PR release-hygiene workflow in skill-arbiter. Use when changes are release-impacting and require synchronized pyproject version, changelog entry, and CI release gate compliance. |
| `skill-auditor` | Audit skill candidates and classify each changed skill as unique or upgrade with severity findings. Use when creating/updating skills, preparing admission evidence, or producing audit JSON for skill-game scoring. |
| `skill-blast-radius-simulator` | Simulate pre-install/pre-enable skill impact and require acknowledgement when risk exceeds thresholds. Use when admitting new skills or evaluating potentially risky updates. |
| `skill-cold-start-warm-path-optimizer` | Measure first-run versus warm-run skill performance and generate prewarm/auto-invoke policy plans. Use when cold starts inflate latency or trigger retry storms. |
| `skill-common-sense-engineering` | Apply practical human common-sense checks before and after coding work. Use when you want to prevent avoidable mistakes, keep changes proportional, and capture obvious hygiene fixes during implementation. |
| `skill-cost-credit-governor` | Govern per-skill credit and token spend with deterministic warn/throttle/disable actions. Use when usage spikes, agent chatter, or budget overruns must be detected and contained. |
| `skill-dependency-fan-out-inspector` | Inspect skill-to-skill dependencies and detect fan-out, cycles, and N+1 invocation risk. Use when scaling skill stacks or diagnosing hidden cross-skill cost/latency amplification. |
| `skill-enforcer` | Enforce cross-repo policy and boundary alignment before completion. Use when a request touches multiple repositories, shared contracts, or policy docs that must stay synchronized. |
| `skill-hub` | Route user requests into the smallest deterministic skill chain. Use when work spans multiple domains or repositories, when lane selection is ambiguous, or when you need ordered skill handoff and loopback criteria before execution. |
| `skill-installer-plus` | Run local-first skill installation with lockdown admission and a learning recommendation loop. Use when adding/updating skills so installs are evidence-gated and future install choices improve from prior outcomes. |
| `skill-trust-ledger` | Keep a local reliability ledger for skills using recorded outcomes and arbiter evidence. Use when deciding whether to trust, restrict, or block skills over time. |
| `skills-consolidation-architect` | Consolidate repository-specific skills into modular, reusable sets. Use when auditing skill overlap, splitting monolithic skills, reducing one-shot skills, defining per-repo core vs advanced skills, and planning safe deprecations with lockdown admission tests. |
| `skills-discovery-curation` | Discover, triage, and prioritize Codex skills for a repository or workspace. Use for one-time audits and recurring curation runs after cross-repo MX3/shim drift scans. |

## Update Rule

Whenever the skill set changes, update this file in the same PR as:
- `AGENTS.md`
- `README.md`
- `CONTRIBUTING.md`
- `SKILL.md`
- `.github/pull_request_template.md`
