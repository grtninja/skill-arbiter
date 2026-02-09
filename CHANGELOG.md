# Changelog

All notable changes to this project are documented in this file.

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
