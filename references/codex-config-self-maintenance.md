# Codex Config Self-Maintenance Public Contract

This public-shape reference describes the safety contract for the `codex-config-self-maintenance` candidate without exposing workstation-specific paths.

## Required Local-Agent Doctrine

- Use candidate-first validation for `config.toml`, profile, MCP, and settings changes.
- Keep trusted folders, local-subagent state, reasoning visibility, and visible action-state parity explicit before promotion.
- Treat `<codex_config_path>` as the live config placeholder and keep direct edits behind parse and assertion gates.
- Repo-backed machine profile checks must include `profiles.json` when profile parity is part of the request.
- Required local-agent doctrine includes `skill-hub`, `request-loopback-resume`, `skill-common-sense-engineering`, `usage-watcher`, `skill-cost-credit-governor`, and `skill-trust-ledger`.

## Evidence Expectations

- Candidate files parse before promotion.
- Active MCP tables are checked as active configuration, not inferred from comments.
- The live file, profile set, and user-visible settings surface are compared before reporting parity.
- Private host paths and raw local evidence remain outside public-shape repo files.
