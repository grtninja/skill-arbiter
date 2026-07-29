# July 23, 2026 Codex / STARFRAME incident index

This index preserves one canonical route per observed failure class. It is evidence and routing infrastructure, not a claim that every item has the same root cause.

## Canonical upstream reports

| Failure class | Canonical route | Status |
|---|---|---|
| Auto-compaction completes but leaves the active thread about 80% full, causing repeat compaction and usage waste | `openai/codex#35032` | Open; independently corroborated; redacted chronology attached |
| Active official incidents are not surfaced inside the running Codex session and usage-heavy runs lack a pause/handoff path | `openai/codex#35038` | Open; `#35037` closed as duplicate |
| Codex claims visible app/tool success after backend-only configuration, before foreground acceptance and rollback verification | `openai/codex#35041` | Open; `#35039` closed as duplicate after rollback requirements were consolidated |
| Account-specific quota reset, entitlement, and rollout events lack authoritative in-product history | `openai/codex#35044` | Open; `#35040`, `#35042`, and `#35045` closed as duplicates |
| Bounded tasks expand into governance/scaffolding loops, false completion, and usage exhaustion | `openai/codex#34898` | Existing canonical issue; PR-level scope-substitution evidence routed from closed duplicate `#35043` |

## Local STARFRAME ownership

| Failure class | Local route |
|---|---|
| `system.status` reports healthy while governed controlled execution times out | `grtninja/Starframe-PC-Control#45` |
| Backlog IDs are incompatible with `local_agent.run.poll`, followed by repeated deterministic failures | `grtninja/Starframe-PC-Control#47` |
| Stored integration state is confused with live provider/tool health | `grtninja/Starframe-PC-Control#49` |
| `review_id` is required without a reliable same-surface create/discover path | `grtninja/Starframe-PC-Control#50` |
| Native visible Qwen read/edit/test/Git loop is incomplete | `grtninja/Starframe-PC-Control#51` |
| PC Control and OpenClaw must remain live while optional failed integrations are quarantined individually | `grtninja/Starframe-PC-Control#56` |
| Requested and effective model/tools/write authority can silently diverge | `grtninja/Starframe-PC-Control#60` |
| Authenticated Hugging Face integration incident requires private evidence-preserving audit | `grtninja/Starframe-PC-Control#61` |
| Security/Safety Bug Bounty candidate intake and disclosure routing | `grtninja/Starframe-PC-Control#68` |
| Mandatory defect reporting and Codex-to-ChatGPT consult during active work | `grtninja/Starframe-PC-Control#69` |
| Session-level usage review/remediation packet | `grtninja/Starframe-PC-Control#70` |

## Evidence

- [Redacted repeated-compaction chronology](https://github.com/grtninja/skill-arbiter/blob/f4e41ea7db5ddf8562767d74c6cf2e088223e3c9/docs/incidents/openai-codex/2026-07-23/codex_compaction_loop_redacted.svg)
- [Evidence manifest and hashes](codex_compaction_loop_evidence.md)
- [Incident reporting and bounty triage SOP](../../INCIDENT_REPORTING_AND_BOUNTY_SOP.md)

## Operating rule

No issue closes because an issue was filed, a plan exists, a large diff was produced, a toggle changed, or backend activity occurred. Closure requires the receiving owner/disposition, a patch or support/bounty outcome, focused regression where applicable, release/merge state, and operator-visible acceptance.
