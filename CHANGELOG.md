# Changelog

All notable changes to this project are documented in this file.

## [0.2.16] - 2026-02-27

### Changed

- Added missing meta-governance candidate skills:
  - `skill-candidates/skill-hub/`
  - `skill-candidates/skill-enforcer/`
  - `skill-candidates/skill-auditor/`
- Added deterministic skill-audit tooling:
  - `skill-candidates/skill-auditor/scripts/skill_audit.py`
  - `tests/test_skill_audit.py`
- Upgraded repo-specific candidate skills to align with current private-repo policy/runtime behavior:
  - `skill-candidates/repo-b-control-center-ops/SKILL.md`
  - `skill-candidates/repo-b-hardware-first/SKILL.md`
  - `skill-candidates/repo-b-hardware-first/references/strict-commands.md`
  - `skill-candidates/repo-b-mass-index-ops/SKILL.md`
  - `skill-candidates/repo-b-mass-index-ops/references/presets.md`
  - `skill-candidates/repo-b-preflight-doc-sync/SKILL.md`
  - `skill-candidates/repo-b-avatarcore-ops/agents/openai.yaml`
  - `skill-candidates/repo-b-starframe-ops/SKILL.md`
  - `skill-candidates/repo-b-starframe-ops/agents/openai.yaml`
  - `skill-candidates/repo-b-starframe-ops/references/starframe-checklist.md`
  - `skill-candidates/repo-b-wsl-hybrid-ops/SKILL.md`
  - `skill-candidates/repo-c-boundary-governance/SKILL.md`
  - `skill-candidates/repo-c-mass-index-ops/SKILL.md`
  - `skill-candidates/repo-c-policy-schema-gate/SKILL.md`
  - `skill-candidates/repo-c-ranking-contracts/SKILL.md`
  - `skill-candidates/repo-c-trace-ndjson-validate/SKILL.md`
  - `skill-candidates/repo-d-mass-index-ops/SKILL.md`
  - `skill-candidates/repo-d-mass-index-ops/references/presets.md`
  - `skill-candidates/repo-d-ui-guardrails/SKILL.md`
  - `skill-candidates/repo-d-ui-guardrails/references/guardrails.md`
  - `skill-candidates/docs-alignment-lock/SKILL.md`
- Updated `references/recommended-skill-portfolio.md` with consolidated runtime core/advanced sets and governance lanes.
- Tightened cross-skill boundaries for repo mass-index and governance lanes to reduce deterministic overlap and dependency cycles reported by local audit tooling.
- Documented VS Code/Codex built-in compatibility and overlay reset recovery workflow:
  - `references/vscode-skill-handling.md`
- Added complete installed-skill catalog and usage/chaining guide for the expanded skill set:
  - `references/skill-catalog.md`
  - `references/usage-chaining-multitasking.md`
- Added Microsoft Edge browser preference skill for deterministic Playwright Edge-channel execution:
  - `skill-candidates/playwright-edge-preference/SKILL.md`
  - `skill-candidates/playwright-edge-preference/agents/openai.yaml`
  - `skill-candidates/playwright-edge-preference/references/edge-commands.md`
- Aligned policy and contribution docs to require catalog/guide synchronization and additive (non-conflicting) VS Code skill handling:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
  - `references/default-skill-system.md`
- Tightened repo-b bridge/comfy boundary wording to preserve capability while reducing deterministic dependency-loop noise in skill graph audits.
- Leveled up core governance skills with stronger deterministic contracts and progression controls:
  - `skill-candidates/skill-hub/SKILL.md`
  - `skill-candidates/usage-watcher/SKILL.md`
  - `skill-candidates/skill-cost-credit-governor/SKILL.md`
  - `skill-candidates/skill-cold-start-warm-path-optimizer/SKILL.md`
  - `skill-candidates/skill-installer-plus/SKILL.md`
  - `skill-candidates/code-gap-sweeping/SKILL.md`
  - `skill-candidates/request-loopback-resume/SKILL.md`
- Added explicit skill progression rubric and maturity tracking:
  - `references/skill-progression.md`

## [0.2.15] - 2026-02-19

### Changed

- Added 2 new Repo B candidates for AvatarCore and STARFRAME runtime changes:
  - `skill-candidates/repo-b-avatarcore-ops/SKILL.md`
  - `skill-candidates/repo-b-starframe-ops/SKILL.md`
- Upgraded `skill-candidates/repo-a-coordinator-smoke/` to include coordinator health/readiness probes in smoke expectations.
- Upgraded `skill-candidates/repo-b-control-center-ops/` to include control-center window manager and Electron launch checks.
- Expanded `skill-candidates/repo-c-shim-contract-checks/` contract coverage for audio/rag fail-closed behavior and replaced `rg`-based local contract scans.
- Updated `references/recommended-skill-portfolio.md` with the two new Repo B skill entries.

## [0.2.14] - 2026-02-14

### Changed

- Enforced usage-saving evaluation as a mandatory chain gate across policy docs:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
- Updated default chain order to explicitly require:
  - `usage-watcher` (mode + usage artifacts),
  - `skill-cost-credit-governor` (spend/chatter policy),
  - `skill-cold-start-warm-path-optimizer` (prewarm decision),
  before downstream mutation/consolidation lanes.
- Upgraded candidate skill workflows to fail closed when usage guardrail evidence is missing:
  - `skill-candidates/usage-watcher/SKILL.md`
  - `skill-candidates/skill-cost-credit-governor/SKILL.md`
  - `skill-candidates/skill-cold-start-warm-path-optimizer/SKILL.md`
  - `skill-candidates/skill-common-sense-engineering/SKILL.md`
  - `skill-candidates/skill-installer-plus/SKILL.md`
  - `skill-candidates/skills-discovery-curation/SKILL.md`
  - `skill-candidates/skills-consolidation-architect/SKILL.md`
- Updated `scripts/skill_game.py` default required chain so usage-saving skills are enforced in workflow scoring by default.

## [0.2.13] - 2026-02-12

### Changed

- Upgraded `skill-candidates/code-gap-sweeping/scripts/code_gap_sweep.py` with working-tree-aware diff support:
  - added `--diff-mode` (`committed`, `working-tree`, `combined`; default `combined`) so sweeps can include unstaged and untracked changes.
  - included untracked file detection in changed-file and TODO/FIXME scans.
  - added backward-compatible default `diff_mode` parameters for direct function callers.
- Tightened TODO/FIXME detection to marker-style additions and added deterministic dedupe/sort on emitted evidence.
- Expanded deterministic tests in `tests/test_code_gap_sweep.py` to cover:
  - release-hygiene checks with explicit diff mode.
  - working-tree mode file selection (including untracked files).
  - combined patch + untracked TODO/FIXME evidence behavior.
- Updated package version to `0.2.13` for release-hygiene lockstep on this script upgrade.

## [0.2.12] - 2026-02-12

### Changed

- Added deterministic unit coverage for newly introduced candidate-skill scripts that were previously flagged as untested:
  - `tests/test_code_gap_sweep.py` for `skill-candidates/code-gap-sweeping/scripts/code_gap_sweep.py`
  - `tests/test_workstream_resume.py` for `skill-candidates/request-loopback-resume/scripts/workstream_resume.py`
  - `tests/test_comfy_media_pipeline_check.py` for `skill-candidates/repo-b-comfy-amuse-capcut-pipeline/scripts/comfy_media_pipeline_check.py`
- Updated package version to `0.2.12` for release-hygiene lockstep on Python test additions.

## [0.2.11] - 2026-02-11

### Changed

- Added new candidate skill `skill-candidates/code-gap-sweeping/`:
  - `scripts/code_gap_sweep.py` for deterministic cross-repo gap scans (`tests_missing`, `docs_lockstep_missing`, `todo_fixme_added`, `release_hygiene_missing`).
  - `scripts/repo_family_pipeline.py` for deterministic full-pipeline command matrices across repo families (`repo_a`/`repo_b`/`repo_c`/`repo_d`) with checkpoint, sweep, and admission command lanes.
  - `references/gap-rubric.md` for severity mapping and remediation lanes.
  - `references/repo-family-pipeline.md` for all-repo pipeline matrix usage and family skill-pack mapping.
  - `agents/openai.yaml` metadata for direct invocation.
- Updated workflow docs to include `code-gap-sweeping` in the multi-repo baseline chain:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
  - `references/recommended-skill-portfolio.md`
- Validated cross-repo sweep execution with machine-readable output (`/tmp/code-gap-sweep-all.json`) and generated admission evidence for `code-gap-sweeping` via:
  - `scripts/arbitrate_skills.py ... --personal-lockdown --json-out /tmp/code-gap-sweeping-arbiter.json`
  - `skill-candidates/skill-installer-plus/scripts/skill_installer_plus.py plan/admit ... --json-out ...`
- Validated full repo-family pipeline matrix generation with machine-readable output and runnable command script:
  - `/tmp/repo-family-pipeline.json`
  - `/tmp/repo-family-pipeline.sh`
- Revalidated upgraded `code-gap-sweeping` admission/evidence after matrix additions:
  - arbiter pass (`/tmp/code-gap-sweeping-arbiter-v2.json`)
  - installer evidence (`/tmp/code-gap-sweeping-installer-plan-v2.json`, `/tmp/code-gap-sweeping-installer-admit-v2.json`)
  - classification surrogate (`/tmp/code-gap-sweeping-classification-v2.json`)
- Upgraded `skill-candidates/repo-b-mcp-comfy-bridge/` to align with current media pipeline surfaces:
  - added workflow/pipeline tool contract guidance for `shim.comfy.workflow.submit` and `shim.comfy.pipeline.run`,
  - added AMUSE and CapCut contract checks (`/api/amuse/*`, profile-level `capcut_export` metadata),
  - refreshed checklist and agent prompt metadata.
- Added new candidate skill `skill-candidates/repo-b-comfy-amuse-capcut-pipeline/`:
  - `scripts/comfy_media_pipeline_check.py` for deterministic preflight checks across MCP, Comfy pipeline profiles, AMUSE status, and CapCut export contract expectations.
  - `references/pipeline-contract.md` for failure modes and required profile contracts.
- Added new candidate skill `skill-candidates/request-loopback-resume/`:
  - `scripts/workstream_resume.py` for deterministic checkpoint/resume state management (`init`, `set`, `validate`, `resume`) across interrupted and multi-lane requests.
  - `references/state-contract.md` for lane status model, invariants, and resume action contract.
- Validated `request-loopback-resume` with deterministic evidence:
  - state validation/resume outputs (`/tmp/request-loopback-resume-validate.json`, `/tmp/request-loopback-resume-resume.json`)
  - arbiter admission (`/tmp/request-loopback-resume-arbiter.json`)
  - installer plan/admit evidence (`/tmp/request-loopback-resume-installer-plan.json`, `/tmp/request-loopback-resume-installer-admit.json`)
  - classification surrogate (`/tmp/request-loopback-resume-classification.json`)
- Updated workflow docs/templates to include `request-loopback-resume` in the default pipeline for interrupted work:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
  - `references/recommended-skill-portfolio.md`

## [0.2.10] - 2026-02-10

### Changed

- Added new candidate skill `skill-candidates/skill-installer-plus/`:
  - `scripts/skill_installer_plus.py` for local-first install planning, lockdown admission orchestration, and feedback-driven recommendation learning.
  - `references/learning-loop.md` for scoring inputs and operating cycle.
  - `agents/openai.yaml` metadata for direct invocation.
- Updated workflow system docs and templates to include `skill-installer-plus` explicitly:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
  - `references/recommended-skill-portfolio.md`
- Updated `scripts/skill_game.py` default required-skill chain to include `skill-installer-plus` so XP scoring reinforces installer-lane usage.
- Added missing `## Loopback` sections to:
  - `skill-candidates/repo-b-control-center-ops/SKILL.md`
  - `skill-candidates/repo-b-local-comfy-orchestrator/SKILL.md`
  - `skill-candidates/repo-b-mcp-comfy-bridge/SKILL.md`
  - `skill-candidates/repo-b-thin-waist-routing/SKILL.md`
- Ran consolidation upgrades for mass-index wrappers and tightened boundaries:
  - `skill-candidates/repo-b-mass-index-ops/SKILL.md`
  - `skill-candidates/repo-c-mass-index-ops/SKILL.md`
  - `skill-candidates/repo-d-mass-index-ops/SKILL.md`
  - overlap audit result improved from `merge_count=3` to `merge_count=0` for candidate skills at threshold `0.28`.

## [0.2.9] - 2026-02-10

### Changed

- Upgraded `scripts/arbitrate_skills.py` to use baseline-normalized churn scoring:
  - added `--baseline-window` sampling before each skill install,
  - evaluates removal on delta samples (`raw - baseline_max`) instead of absolute host process count,
  - emits both normalized and raw sampling fields in JSON evidence for forensics.
- Added `scripts/skill_game.py` to make workflow compliance game-like with deterministic scoring:
  - persistent local XP/level/streak ledger,
  - scoring for required gate usage (`skill-hub`, `skill-common-sense-engineering`, `skill-auditor`, `skill-enforcer`, `skill-arbiter-lockdown-admission`),
  - arbiter/auditor/enforcer evidence bonuses and penalties.
- Synchronized workflow docs and templates for the game loop and new baseline option:
  - `AGENTS.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `SKILL.md`
  - `.github/pull_request_template.md`
  - `references/recommended-skill-portfolio.md`

## [0.2.8] - 2026-02-10

### Changed

- Upgraded `skill-candidates/skill-auditor/scripts/skill_audit.py` to enforce mandatory skill-governance checks:
  - optional `--arbiter-report` ingestion with `--require-arbiter-evidence` fail-closed behavior.
  - explicit per-skill classification output (`unique` vs `upgrade`) with nearest-peer overlap score.
  - deterministic focused mode via `--only-include-skill` for targeted audits.
- Upgraded `skill-candidates/skill-hub/scripts/skill_hub_route.py` and related docs to require:
  - arbiter pass evidence for new/updated skills,
  - `skill-auditor` classification capture (`unique` vs `upgrade`),
  - loopback reroutes when classification/boundary decisions are unresolved.
- Updated governance candidate skill docs and references to align with mandatory gates:
  - `skill-candidates/skill-hub/`
  - `skill-candidates/skill-auditor/`
  - `skill-candidates/skill-enforcer/`
  - `skill-candidates/skills-discovery-curation/`
  - `skill-candidates/skills-cross-repo-radar/`
  - `skill-candidates/skills-consolidation-architect/`
- Synchronized policy docs (`AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `SKILL.md`, `.github/pull_request_template.md`, `references/recommended-skill-portfolio.md`) so skill-change workflow now explicitly requires:
  - arbiter pass verification,
  - unique-vs-upgrade classification,
  - consolidation-first handling for upgrade classifications.

## [0.2.7] - 2026-02-10

### Changed

- Consolidated repo-b Comfy/MCP skill boundaries:
  - `skill-candidates/repo-b-mcp-comfy-bridge/` is now the canonical lane for MCP adapter + `shim.comfy.*` diagnostics, with explicit fail-closed checks.
  - `skill-candidates/repo-b-local-comfy-orchestrator/` now acts as a legacy compatibility wrapper that routes new work to `repo-b-mcp-comfy-bridge`.
- Tightened scope in `skill-candidates/repo-b-local-bridge-orchestrator/` to explicit `/api/agent` orchestration and guidance-hint validation, excluding MCP/Comfy diagnostics.
- Added new candidate skill `skill-candidates/skills-cross-repo-radar/`:
  - `scripts/repo_change_radar.py` for recurring multi-repo MX3/shim signal scans.
  - `references/radar-playbook.md` for cadence and triage thresholds.
- Added new candidate skill `skill-candidates/skill-common-sense-engineering/`:
  - practical human common-sense sanity checks for right-sized changes and obvious hygiene misses.
  - `references/common-sense-checklist.md`.
- Added new candidate skill `skill-candidates/skill-auditor/`:
  - `scripts/skill_audit.py` for deterministic audits of recently changed/new skills.
  - `references/audit-rubric.md`.
- Added new candidate skill `skill-candidates/skill-enforcer/`:
  - `scripts/skill_enforce.py` for cross-repo required-skill reference enforcement.
  - `references/enforcement-policy.md`.
- Added new candidate skill `skill-candidates/skill-hub/`:
  - `scripts/skill_hub_route.py` for baseline-first skill-chain routing.
  - `references/routing-matrix.md`.
- Upgraded `skill-candidates/skill-arbiter-lockdown-admission/` to include:
  - pre-admission artifact hygiene scanning and cleanup in workflow/checklist text.
  - new `scripts/artifact_hygiene_scan.py` for deterministic detection/removal of generated artifacts.
  - explicit maintenance trigger to update the skill when new recurring artifact patterns are observed.
- Upgraded `skill-candidates/skills-discovery-curation/` to include recurring multi-repo curation flow using `skills-cross-repo-radar` and baseline system-chain routing via `skill-hub`.
- Upgraded `skill-candidates/skill-hub/` to support loopback-capable routing and natural multitask decomposition:
  - baseline chain + parallel workstreams + merge chain output.
  - explicit loopback triggers/stop conditions via `references/loopback-protocol.md`.
  - auto-inclusion guidance for `multitask-orchestrator` when independent lanes are present.
- Ran `skill-auditor` against recent skill additions and resolved flagged workflow-structure gaps in mass-index skill wrappers/core.
- Updated discovery/admission documentation in `README.md`, `SKILL.md`, and `references/recommended-skill-portfolio.md` to reflect canonical vs legacy repo-b Comfy routing and the new always-on governance system (`skill-hub`, `skill-common-sense-engineering`, `skill-auditor`, `skill-enforcer`).
- Updated `skill-candidates/skill-trust-ledger/SKILL.md` examples to use `repo-b-mcp-comfy-bridge` evidence naming.

## [0.2.6] - 2026-02-09

### Added

- New candidate skill `skill-candidates/skill-cost-credit-governor/`:
  - `scripts/skill_cost_governor.py` for spend/risk analysis and `warn|throttle|disable` policy output.
  - `references/governor-workflow.md`
  - `references/policy-contract.md`
- New candidate skill `skill-candidates/skill-dependency-fan-out-inspector/`:
  - `scripts/dependency_inspector.py` for dependency graph, cycle detection, fan-out hotspots, and N+1 risk reporting.
  - `references/inspection-workflow.md`
  - `references/graph-contract.md`
- New candidate skill `skill-candidates/skill-cold-start-warm-path-optimizer/`:
  - `scripts/warm_path_optimizer.py` for cold-vs-warm analysis and prewarm planning.
  - `references/optimizer-workflow.md`
  - `references/latency-contract.md`
- New candidate skill `skill-candidates/skill-blast-radius-simulator/`:
  - `scripts/blast_radius_sim.py` for pre-admission risk scoring and acknowledgement gating.
  - `references/simulation-workflow.md`
  - `references/risk-heuristics.md`
- New candidate skill `skill-candidates/skill-trust-ledger/`:
  - `scripts/trust_ledger.py` for event recording, arbiter ingest, and trust-tier reports.
  - `references/ledger-workflow.md`
  - `references/scoring-contract.md`

### Changed

- Updated `README.md`, `SKILL.md`, and `references/recommended-skill-portfolio.md` to include discovery and admission guidance for the five new meta-governance skills.

## [0.2.5] - 2026-02-09

### Added

- New candidate skill `skill-candidates/repo-b-local-comfy-orchestrator/` for reliability-first local Comfy MCP resource orchestration in `<PRIVATE_REPO_B>`.
- New reference set for the skill:
  - `references/orchestrator-workflow.md`
  - `references/validation-contract.md`
  - `references/phase2-prompt-lifecycle-roadmap.md`
- New drop-in `<PRIVATE_REPO_B>` hook templates under `assets/repo_b/`:
  - `tools/local_comfy_orchestrator.py`
  - `tools/local_comfy_validate.py`
  - `tools/local_comfy_orchestrator.example.env`
  - `tests/tools/test_local_comfy_orchestrator.py`
  - `tests/tools/test_local_comfy_validate.py`

### Changed

- Updated `README.md`, `SKILL.md`, and `references/recommended-skill-portfolio.md` to include admission/discovery guidance for `repo-b-local-comfy-orchestrator`.

## [0.2.4] - 2026-02-09

### Added

- New candidate skill `skill-candidates/repo-b-local-bridge-orchestrator/` for credit-first local bridge orchestration in `<PRIVATE_REPO_B>`.
- New reference set for the skill:
  - `references/orchestrator-workflow.md`
  - `references/validation-contract.md`
  - `references/mx3-phase2-roadmap.md`
- New drop-in `<PRIVATE_REPO_B>` hook templates under `assets/repo_b/`:
  - `tools/local_bridge_orchestrator.py`
  - `tools/local_bridge_validate.py`
  - `tools/local_bridge_orchestrator.example.env`
  - `tests/tools/test_local_bridge_orchestrator.py`
  - `tests/tools/test_local_bridge_validate.py`

### Changed

- Updated `README.md`, `SKILL.md`, and `references/recommended-skill-portfolio.md` to include admission/discovery guidance for `repo-b-local-bridge-orchestrator`.

## [0.2.3] - 2026-02-09

### Added

- New candidate skill `skill-candidates/usage-watcher/` for usage burn-rate analysis and budget/rate-limit guardrails:
  - `scripts/usage_guard.py` for usage history analysis and budget planning
  - `references/cost-control-playbook.md`
  - `references/usage-csv-template.csv`

### Changed

- Added `usage-watcher` export/admission references to `README.md`, `SKILL.md`, `references/publish-notes.md`, and `references/recommended-skill-portfolio.md`.

## [0.2.2] - 2026-02-09

### Added

- New core candidate skill `skill-candidates/safe-mass-index-core/` with deterministic metadata-only indexing scripts:
  - `scripts/index_build.py` (bounded incremental/full build with budgets and optional sharded storage)
  - `scripts/index_query.py` (local artifact query by path/ext/lang/size/freshness/scope)
- New wrapper candidate skills that delegate to `safe-mass-index-core` presets:
  - `skill-candidates/repo-b-mass-index-ops/`
  - `skill-candidates/repo-d-mass-index-ops/`
  - `skill-candidates/repo-c-mass-index-ops/` (default sharded profile for very large repos)
- Index schema reference doc: `skill-candidates/safe-mass-index-core/references/index-schema.md`.

### Changed

- README candidate skill catalog now includes the new mass-index skill family.
- `references/recommended-skill-portfolio.md` now includes a large-repo mass-index recommendation and lockdown admission template for the new skills.
- `SKILL.md`, `CONTRIBUTING.md`, `.github/pull_request_template.md`, and `references/publish-notes.md` now include export-readiness guidance for skill-arbiter evidence reporting on new/updated skills.

## [0.2.1] - 2026-02-09

### Added

- Repository policy source file `AGENTS.md` with consolidated operational, release, and privacy rules.
- Hard privacy gate script `scripts/check_private_data_policy.py` to block private repo identifiers and user-specific absolute paths.
- Local hook bootstrap `scripts/install_local_hooks.sh` plus tracked pre-commit hook at `.githooks/pre-commit`.
- New candidate skill `skill-candidates/docs-alignment-lock/` for docs-policy alignment and pre-PR privacy/release checks.

### Changed

- CI now enforces `python3 scripts/check_private_data_policy.py` and compiles the new checker script.
- PR template validation now includes privacy policy and docs-alignment checks.
- Documentation set (`README.md`, `CONTRIBUTING.md`, `SKILL.md`) now documents the privacy lock workflow.
- Candidate skill docs were sanitized to placeholder-based repo/path references instead of private identifiers.
- Candidate skill folder/name surfaces were redacted to neutral `repo-a`/`repo-b`/`repo-c`/`repo-d` naming.
- Added a standard skill progress declaration format:
  - `New Skill Unlocked: <SkillName>`
  - `<SkillName> Leveled up to <LevelNumber>`

## [0.2.0] - 2026-02-09

### Added

- Support for local whitelist and immutable skill files:
  - `--whitelist` (`.whitelist.local` by default)
  - `--immutable` (`.immutable.local` by default)
- Support for promoting passing skills with `--promote-safe`.
- Personal lock-down mode via `--personal-lockdown`:
  - requires local `--source-dir`
  - auto-promotes passing skills to whitelist + immutable
  - rejects symlinked control files and symlinked local skill paths
- Validation for skill names and list filename arguments.
- Optional local source install flow via `--source-dir` in the CLI contract docs.
- Release automation helpers:
  - `scripts/prepare_release.py` for version bump + changelog entry scaffolding.
  - `scripts/check_release_hygiene.py` for PR release-gate validation.
- Repository metadata files for dependency and build declarations (`requirements.txt`, richer `pyproject.toml` fields).

### Changed

- `--max-rg` is now constrained to `1-3` with `3` as the hard maximum safety rail.
- Blacklisting behavior is permanent within this tool's policy:
  blacklisted skills are denied and deleted if present.
- Third-party repo-based candidates are deny-by-default unless explicitly promoted.
- CI now enforces release hygiene on pull requests for release-impacting changes.
- Documentation and PR template now include a standard release-before-PR workflow.

## [0.1.0] - 2026-02-09

### Added

- Initial public release of `skill-arbiter`.
- Core arbitration loop:
  install candidate skill, sample `rg.exe` process churn, remove noisy skills, and persist blacklist decisions.

