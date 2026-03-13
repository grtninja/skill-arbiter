# skill-arbiter Project Scope

This document is the canonical high-level scope for `skill-arbiter`.

## Product identity

`skill-arbiter` is a Windows-first NullClaw host security app with:

- embedded desktop operator UI
- loopback-only local arbitration agent
- curated-source discovery and upgrade reconciliation
- Codex app, VS Code, and GitHub Copilot instruction-surface interoperability tracking
- local Codex config and loopback LM Studio coding-model interoperability
- active threat suppression for hostile skills and related automation surfaces
- strict self-governance and public-shape publication controls
- branded desktop launch surfaces, support/about metadata, and public-release readiness checks
- case-based mitigation workflow for quarantine, strip, rebuild, blacklist, and rescan loops
- layered operator UI with explicit startup, critical queue, active finding, mitigation, and evidence layers
- ownership and legitimacy scoring for official built-ins, repo-owned skills, candidate-only skills, and unowned local installs

## Current operating truth

- The app has a valid standalone local lane for inventory, baseline reconciliation, attribution, and mitigation.
- The app is only fully effective when the surrounding work is being driven by Codex app or GitHub Copilot instruction surfaces.
- Collaboration learning, skill-game progression, and upgrade/consolidation recommendation lanes are intentionally downstream of real Codex/Copilot-driven work and should be described as partial otherwise.
- AI/agent-assisted output remains advisory and fallible; operator review is part of the scope, not an optional extra.

## Scope lanes

- Local skill inventory and baseline reconciliation
- Curated-source and threat-matrix discovery for OpenClaw / NullClaw surfaces
- Admission, quarantine, and operator-confirmed remediation
- Case-based mitigation and adjacent-vector follow-through
- Privacy/public-shape enforcement
- Self-governance and release-surface auditing
- Public support/about surfacing without browser auto-launch
- Cross-repo recent-work relevance for skill prioritization
- Local loopback coding-model advisor integration for short coding-security guidance, with Qwen preference by default

## Out of scope

- Ownership of runtime inference execution in STARFRAME or MX3 repos
- Persona execution ownership
- Remote bind/listen behavior for the local agent
- Automatic destructive cleanup without operator confirmation

See `docs/SCOPE_TRACKER.md` for current completion state.
