# Changelog

All notable changes to this project are documented in this file.

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
  - `New Skill Unlocked`
  - `<Skill Name> leveled up to XX`

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
