# Cross-Surface Parity Notes

Parity checks should cover:

1. Candidate config (`%USERPROFILE%\.codex\config.toml`) syntax and keys.
2. Repo profile tomls under `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles`.
3. VS Code user MCP declarations in `%USERPROFILE%\AppData\Roaming\Code\User\mcp.json`.
4. Copilot MCP declarations in `%USERPROFILE%\.copilot\mcp-config.json`.
5. Continue home MCP declarations in `%USERPROFILE%\.continue\mcpServers`.
6. Continue workspace MCP declarations in `C:\STARFRAME-Continue-Codex-Workspace\.continue\mcpServers`.
7. Repo-backed Continue template declarations in `G:\GitHub\<PRIVATE_REPO_B>\integrations\continue-meta-harness\mcpServers`.
8. MCP panel expectations by validating active `[mcp_servers.*]` tables, not commented examples.
9. Manual review of `profiles.json` when adding/removing machine profile files.

Use `validate_candidate.py --parity-profile` to compare:

- Contract keys (`model`, reasoning keys, and display flags).
- Required MCP IDs.
- `starframe-local-mcp.env` required STARFRAME variables.
- JSON MCP declaration surfaces that should expose the same required MCP ids.
- Wrapper fragments for newline-only local stdio MCP servers:
  - `codex-local=codex_local_stdio_entry.py`
  - `vera-retrieval=vera_stdio_bridge_entry.py`
  - `playwright-mcp-edge=playwright_stdio_bridge_entry.py`
  - `serena=serena_stdio_bridge_entry.py`
