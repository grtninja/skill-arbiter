# Manifest Evidence

Use this file as the manifest of cross-surface checks for this skill.

- Candidate scope
  - `scripts/validate_candidate.py`
  - `references/config-contract.md`
- Contract surfaces
  - Live config: `%USERPROFILE%\.codex\config.toml`
  - Repo-backed profiles: `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\*.toml`
  - MCP evidence: active `[mcp_servers.*]` tables only

- Evidence targets
  - Main model and reasoning keys are consistent across candidate + profiles.
  - Required MCP server IDs exist on both candidate and each profile.
  - `starframe-local-mcp` env keeps required STARFRAME endpoints and skill-arbiter keys.
