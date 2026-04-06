# skill-arbiter Scope Tracker

## Snapshot

- **Last updated:** 2026-04-05
- **OVERALL PROJECT COMPLETION:** 93%
- **MVP COMPLETION:** 95%
- **Primary operating mode:** local-first NullClaw host security app
- **Important limitation:** fully meaningful interop/collaboration/skill-learning behavior still depends on real Codex or GitHub Copilot-driven work; standalone desktop mode is partial outside that lane

## Segment Status

| Segment | Completion | Evidence |
| --- | --- | --- |
| Runtime / core features | 94% | loopback agent, local inventory, legitimacy scoring, case-based mitigation, self-governance, desktop shell entrypoint, collaboration lane, stack-accounting ingestion, quest runtime, and live local supervisor runtime |
| Integrations / contracts | 90% | OpenAI built-in baseline reconcile, curated-source parsing, Codex/VS Code/Copilot interop tracking, OpenClaw / NullClaw threat matrix integration, SkillHub discovery-only intake, and local OpenAI-compatible model-host fallback |
| Validation / tests | 89% | privacy, self-governance, inventory, API, supply-chain, mitigation, public-release, collaboration, quest-runtime, stack-accounting, and SkillHub/runtime integration tests |
| Packaging / operations | 74% | desktop launcher, branded icon lane, shortcut installer, startup acceptance tightening, and public-release gate wired; packaged binary distribution still incomplete |
| Governance / docs | 95% | boundaries, security, contribution, scope, README, generated catalog, generated vetting report, SkillHub alignment references, meta-harness authority notes, and public-release guidance updated |

## Completed in this pass

1. Added the `skill_arbiter` runtime package and loopback API.
2. Added the embedded desktop UI and app-first startup flow.
3. Added shared privacy scanning and self-governance scanning.
4. Added local Qwen advisor plumbing with local-only defaults.
5. Added machine-generated skill catalog refresh.
6. Added tests for privacy, self-governance, inventory, and agent API.
7. Removed the current tracked privacy leak in `vrm-material-lighting-debug`.
8. Added public release readiness checks, support/about metadata, and branded desktop launch surfaces.
9. Added workspace interop inventory for Codex app, VS Code, and GitHub Copilot instruction surfaces.
10. Added ownership/legitimacy scoring so official built-ins, repo-owned skills, and hostile skills are separated explicitly.
11. Added machine-generated skill vetting report and mitigation runbook metadata.
12. Expanded the advisor lane to support loopback-local model interoperability while preserving meta-harness authority semantics: `:9000` public plane first, `:2337` hosted large-model lane second, and `:1234` as an operator surface only.
13. Restructured the desktop UI into a layered operator flow with critical-first triage, stronger on/off states, and severity-color differentiation.
14. Added live stack accounting ingestion (`skill_arbiter.stack_accounting`) so governed skills can consume `TPK`, authoritative cost, displacement preview, benchmark API equivalent cost, routing provenance, and runtime latency directly from the local stack.
15. Upgraded `usage-watcher`, `local-compute-usage`, and `skill-cost-credit-governor` to reason from dual-ledger runtime evidence instead of only manual credit logs or fallback token math.
16. Restored original skill lineage as a live skill-game signal instead of treating it as a deprecated legacy-only display, preserving longitudinal skill maturity and upgrade history.
17. Completed the governed skill sweep with candidate audit, artifact cleanup, overlap detection, and public/privacy gate revalidation after the reconciliation pass.
18. Added SkillHub Phase 1 bounded intake with discovery-only source reputation, first-wave shortlist evidence, and alignment matrix generation.
19. Upgraded the desktop/runtime contract with `/v1/agent-runtime/status`, local VS Code/task observation, and live loopback advisor fallback across local model hosts.
20. Tightened public-shape docs so the repo no longer depends on one private workstation topology or maintainer-name attribution in repo-facing release metadata.
21. Tightened desktop startup acceptance and meta-harness authority docs so public launch guidance now prefers shell-free desktop surfaces and distinguishes `9000`/`2337` authority from `1234` operator-only visibility.
22. Began the meta-harness publication pass across candidate skills and public docs so legacy `Documents\GitHub` aliases, direct `:1234` authority assumptions, and empty-shell startup tolerance are treated as publish blockers.
23. Added a first-class quest runtime and API so substantial work can be tracked as a human-readable request -> chain -> checkpoints -> usable outcome path.
24. Wired quest completion into the skill game so per-skill quest XP contributes to explicit cumulative agent progression instead of leaving agent leveling implicit.
25. Marked Meta-Harness implementation work as quest-grade by default so authority recovery, bridge validation, and end-state proof can be tracked end to end.

## Remaining gaps

1. Desktop packaging and signed distributable verification beyond the Python-hosted shell.
2. Multi-host federation beyond the local-first `host_id` contract.
3. Deeper cross-repo runtime orchestration hooks for app bring-up and host succession control.
4. Broader machine-generated source matrix/reporting for all tracked external catalogs beyond the current SkillHub first wave.
5. Richer Copilot/Codex instruction drift diffing beyond presence-level interop tracking.
6. Signed packaged desktop distribution and installer verification.
7. A stronger standalone operator mode that keeps collaboration, skill-game, and recommendation lanes richly populated even when governed Codex/Copilot-driven work is temporarily light.
8. Richer quest authoring helpers and template generation so common chains can be opened as active quests before execution instead of only being recorded at closeout.
