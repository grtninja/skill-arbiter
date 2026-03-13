# skill-arbiter Scope Tracker

## Snapshot

- **Last updated:** 2026-03-12
- **OVERALL PROJECT COMPLETION:** 86%
- **MVP COMPLETION:** 91%
- **Primary operating mode:** local-first NullClaw host security app
- **Important limitation:** fully meaningful interop/collaboration/skill-learning behavior still depends on real Codex or GitHub Copilot-driven work; standalone desktop mode is partial outside that lane

## Segment Status

| Segment | Completion | Evidence |
| --- | --- | --- |
| Runtime / core features | 89% | loopback agent, local inventory, legitimacy scoring, case-based mitigation, self-governance, desktop shell entrypoint, collaboration lane, and stack-accounting ingestion |
| Integrations / contracts | 84% | OpenAI built-in baseline reconcile, curated-source parsing, Codex/VS Code/Copilot interop tracking, OpenClaw / NullClaw threat matrix integration, and live local stack accounting inputs for governed usage skills |
| Validation / tests | 82% | privacy, self-governance, inventory, API, supply-chain, mitigation, public-release, collaboration, and stack-accounting integration tests |
| Packaging / operations | 66% | desktop launcher, branded icon lane, shortcut installer, and public-release gate wired; packaged binary distribution still incomplete |
| Governance / docs | 90% | boundaries, security, contribution, scope, skill docs, generated catalog, generated vetting report, public-release guidance, and dual-ledger / skill-lineage reconciliation updated |

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
12. Expanded the advisor lane to support any loopback LM Studio coding model with local-Qwen preference.
13. Restructured the desktop UI into a layered operator flow with critical-first triage, stronger on/off states, and severity-color differentiation.
14. Added live stack accounting ingestion (`skill_arbiter.stack_accounting`) so governed skills can consume `TPK`, authoritative cost, displacement preview, benchmark API equivalent cost, routing provenance, and runtime latency directly from the local stack.
15. Upgraded `usage-watcher`, `local-compute-usage`, and `skill-cost-credit-governor` to reason from dual-ledger runtime evidence instead of only manual credit logs or fallback token math.
16. Restored original skill lineage as a live skill-game signal instead of treating it as a deprecated legacy-only display, preserving longitudinal skill maturity and upgrade history.
17. Completed the governed skill sweep with candidate audit, artifact cleanup, overlap detection, and public/privacy gate revalidation after the reconciliation pass.

## Remaining gaps

1. Desktop packaging and signed distributable verification beyond the Python-hosted shell.
2. Multi-host federation beyond the local-first `host_id` contract.
3. Deeper cross-repo runtime orchestration hooks for app bring-up and host succession control.
4. Broader machine-generated source matrix/reporting for all tracked external catalogs.
5. Richer Copilot/Codex instruction drift diffing beyond presence-level interop tracking.
6. Signed packaged desktop distribution and installer verification.
7. A truly standalone operator mode that does not rely on Codex/Copilot-driven work to make collaboration, skill-game, and recommendation lanes useful.
