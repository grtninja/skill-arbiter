# Online Grounding

This reference records the external-doc basis for the dated-version tracking and safe config workflow. Re-check the sources when changing durable defaults.

## OpenAI Codex

- Source: `https://developers.openai.com/codex/config-reference`
- Verified: `2026-04-24`
- Relevant rules:
  - `model` is the configured Codex model, with `gpt-5.5` used as the current example.
  - `model_reasoning_effort` supports `minimal`, `low`, `medium`, `high`, and `xhigh`, with model-dependent support.
  - `review_model` can override `/review`; otherwise it defaults to the current session model.
  - `mcp_servers.<id>.required = true` fails startup/resume if that enabled MCP server cannot initialize.

## OpenAI Codex On Windows

- Source: `https://developers.openai.com/codex/windows`
- Verified: `2026-04-24`
- Relevant rules:
  - Native Windows Codex can use `elevated` or `unelevated` sandbox modes.
  - `elevated` is the stronger preferred native sandbox; `unelevated` is a weaker fallback.
  - Full access mode can allow destructive actions and data loss; keep sandbox boundaries where possible.
  - Troubleshooting should start from sandbox mode, Windows version, policy errors, filesystem permissions, and `.sandbox/sandbox.log`.
  - Do not send `.sandbox-secrets` contents in diagnostics.

## VS Code Settings And Profiles

- Sources:
  - `https://code.visualstudio.com/docs/configure/settings`
  - `https://code.visualstudio.com/docs/configure/profiles`
  - `https://code.visualstudio.com/docs/configure/settings-sync`
  - `https://code.visualstudio.com/docs/editing/workspaces/workspace-trust`
- Verified: `2026-04-24`
- Relevant rules:
  - Windows user settings path: `%APPDATA%\Code\User\settings.json`.
  - Windows profile settings path: `%APPDATA%\Code\User\profiles\<profile ID>\settings.json`.
  - Profile settings are scoped to the active profile.
  - Settings Sync can sync Settings, UI State, Extensions, and Profiles.
  - Machine and machine-overridable settings are not synced by default.
  - Sync conflicts should be resolved by accepting local, accepting remote, or manual merge.
  - Workspace Trust exists to prevent unintended code execution; when in doubt, restricted mode is safer.

## Local Workflow Consequences

- Do not edit VS Code sync cache files as a substitute for live settings/profile files. Edit live JSON with backup/candidate/validation, then let VS Code sync reconcile.
- Do not hard-require volatile MCP servers during startup unless the user explicitly accepts startup/resume failure as the desired behavior.
- Treat sandbox folders as runtime state. Current `.sandbox` is read-only unless explicitly resetting sandbox; `.sandbox.broken` can be moved as evidence.
- Treat profile associations and `settings.json` as profile-sensitive; back up and validate JSON before promotion.
