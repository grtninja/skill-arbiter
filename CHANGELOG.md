# Changelog
All notable changes to this project are documented in this file.

## [Unreleased]

### Fixed

- upgrade `apps/nullclaw-desktop` from `electron ^35.7.5` to `^39.8.6` to clear the current Dependabot/Electron advisory set for the local security console
- make desktop startup attach against a minimal loopback readiness endpoint so transient advisor/runtime probe failures do not immediately close the Electron shell
- harden local advisor model discovery against loopback connection resets and keep cold-start runtime supervision lighter until the dedicated runtime status lane refreshes
- consolidate the public desktop launch path behind a hidden `pythonw` helper so the VBS/shortcut surface no longer spawns Electron directly during startup
- stop bootstrap-time `git` and trust-ledger subprocesses from flashing visible Windows shells when the loopback agent runs under the no-console desktop backend
- avoid duplicate privacy rescans during startup self-check and public-readiness passes, and move non-essential dashboard panel hydration off the critical startup path
- centralize the hidden Windows subprocess contract in shared runtime/path helpers so startup, release gates, and inventory-side scans reuse one modular no-window implementation
- split inventory, stack-runtime, and agent-server orchestration behind smaller helper modules while keeping the existing test and API entry points stable
- restore the modular desktop UI entry script at `apps/nullclaw-desktop/ui/app.js` so the HTML shell still boots through the current module graph

### Changed

- split the desktop UI into explicit entry, runtime, DOM, polling, runtime-view, and inventory-view modules so the shell no longer depends on a single monolithic `app.js`
- break inventory and collaboration runtime code into smaller helper modules so meta-harness policy, source/baseline attribution, and collaboration evidence handling stay modular and easier to validate

## [0.2.27] - 2026-07-29

### Changed

- publish a public-safe, self-contained redacted exhibit documenting the repeated Codex Desktop automatic-compaction loop for the canonical upstream issue

## [0.2.26] - 2026-05-15

### Changed

- Harden repo-family, mass-index, and cross-repo radar helpers against unsafe repo names, artifact path escapes, symlink pivots, and inherited Git execution hooks.
- Tighten loopback CORS, advisor inventory, privacy, quarantine, and public-release safeguards with regression coverage for Codex Security hardening surfaces.
- Add public skill catalog metadata (#4)
- Add repository code owners
- Level up white-hat for GitHub and supply-chain hardening
- Add white-hat skill and refresh catalog
- Fix external review hygiene self-scan
- Harden external skill review hygiene
- Refresh SkillHub alignment ledgers
- Reconcile repo-owned candidate skills into Codex

## [0.2.25] - 2026-04-21

### Changed

- add a repo-owned `skill-catalog.md` discovery index alongside `references/skill-catalog.md`
- add explicit `author` and `canonical_source` metadata to the repo root skill plus `repo-b-hardware-first` and `white-hat`
- make the public skill-catalog generator fail closed on untracked-skill discovery and omit provenance/description when metadata is not explicitly declared
- align README, CONTRIBUTING, and SKILL guidance with the root catalog output and add regression coverage for tracked discovery behavior

## [0.2.24] - 2026-04-01

### Fixed

- make public-release readiness fail on untracked publish-surface files so clean checkouts match the audited repo state
- make release-hygiene inspect open working-tree and untracked release-impacting changes instead of only committed diff against merge-base
- tighten meta-harness candidate auditing for canonical `G:\GitHub` roots, authoritative `:9000/:2337` model lanes, and `:1234` operator-surface-only wording
- lock the public desktop launch contract to shell-free `wscript`/VBS surfaces and treat empty `cmd.exe`/`powershell.exe`/`pwsh.exe` startup flash as a failure

### Changed

- add `skill_arbiter/meta_harness_policy.py` and wire it into public-readiness plus candidate-skill audit flows
- align README, AGENTS, CONTRIBUTING, SKILL, scope docs, and PR checklist around the meta-harness rollout, the no-empty-shell startup rule, and the skill-game being part of the app harness
- update meta-harness-sensitive candidate skills for canonical root, PC Control-first evidence, hosted `:2337` lane authority, and LM Studio `:1234` operator-only guidance
- refresh generated skill catalog and SkillHub alignment artifacts after the curation and publication pass
## [0.2.23] - 2026-03-27

### Fixed

- replace token-shaped secret-hygiene test literals with runtime-generated fixtures so the public repo no longer trips published secret scanning
- treat host-recognized Codex baseline additions as higher precedence than imported third-party attribution so baseline additions are not misclassified as blocked hostile
- reconcile local system baseline additions and third-party candidate suppression in the live inventory so `plugin-creator` and research-only candidates do not inflate active review counts

### Changed

- split `references/vscode-codex-baseline-additions.md` into top-level and system sections so inventory reconciliation can classify both surfaces consistently
- refresh the generated catalog, vetting report, and VS Code Codex matrix to match the corrected live inventory contract

## [0.2.22] - 2026-03-27

### Fixed

- prevent stale loopback GET caching from leaving the embedded desktop on old inventory, skill-game, or collaboration state
- surface skill-game and collaboration refresh failures in the desktop UI instead of silently leaving zero/default placeholders
