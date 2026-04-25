# Codex Config Maintenance Contract

Use this reference when maintaining Codex config safely for the STARFRAME stack.

## Proven Rules

1. Start from the live file, but do not patch it first.
2. Build a temp candidate and parse it with `tomllib`.
3. Validate the targeted keys, not just general syntax.
4. Treat the Codex settings MCP panel as evidence about active tables, not comments.
5. If the UI only shows one MCP server, the live file likely only has one active server stanza.
6. Replace stale comment examples with active tables only when the candidate parses green.
7. For fragile config changes, prefer manual operator replacement after validation.
8. Record version-sensitive assumptions with `$dated-version-tracking` before treating them as durable.
9. Use `%USERPROFILE%\.codex\config.stale` as the cleanup and evidence lane for historical configs, failed configs, and explicitly broken config artifacts.

## Current High-value Keys

- `model = "gpt-5.5"`
- `review_model = "gpt-5.5"`
- `model_reasoning_effort = "xhigh"`
- `model_reasoning_summary = "detailed"`
- `show_raw_agent_reasoning = true`
- `hide_agent_reasoning = false`
- `model_supports_reasoning_summaries = true`
- `plan_mode_reasoning_effort = "xhigh"`

## Dated Version Assumption

- Effective date: `2026-04-23`
- Verified date: `2026-04-24`
- Claim: GPT-5.5 is the active STARFRAME Codex main/review model contract; GPT-5.4 must not be used as latest/default/main-lane after the effective date unless the reference is explicitly historical.
- Evidence: official OpenAI model docs and GPT-5.5 migration guide, plus the local dated-version ledger.
- Refresh rule: re-check official OpenAI docs before changing model defaults or resolving "current/latest" model claims.

## Config.stale Buckets

- `Current Config`: copied live snapshots for comparison only.
- `Past Good Configs`: parseable historical configs. These are evidence, not promotion candidates until revalidated.
- `Broken Configs`: failed configs, forbidden-key experiments, parse failures, and explicitly broken artifacts.

Required cleanup commands:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\inventory_codex_home.py --write
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --dry-run --require-preflight
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --require-preflight
```

The cleanup must not move `auth.json`, live `config.toml`, active SQLite/WAL/SHM files, sessions, logs, or `.sandbox`.

## Read-only Default

Config, sandbox, and VS Code profile/settings files are read-only until preflight passes. A valid preflight proves the live config is still the 5.5/xhigh/starframe contract, the intended operation has been dry-run, a root inventory was written, active runtime state is excluded, and the dated-version ledger records the assumption or request that made the edit necessary.

## Current Expected MCP Servers

- `starframe-local-mcp`
- `codex-local`
- `openaiDeveloperDocs`

## Current Expected Runtime/Guardrail Sections

- `[analytics]`
- `[otel]`
- `[agents]`
- `[projects.*]`
- `[[skills.config]]`
- `[features]`

## Current Expected Trusted Projects

- `C:\STARFRAME-Continue-Codex-Workspace`
- `G:\GitHub\<PRIVATE_REPO_A>`
- `G:\GitHub\<PRIVATE_REPO_C>`
- `G:\GitHub\<PRIVATE_REPO_B>`
- `<PRIVATE_REPO_ROOT>`

## Current Expected MCP Authority Values

- `STARFRAME_MCP_SHIM_URL = "http://127.0.0.1:9000"`
- `STARFRAME_MCP_SHIM_V1_URL = "http://127.0.0.1:9000/v1"`
- `STARFRAME_HOSTED_V1_URL = "http://127.0.0.1:2337/v1"`
- `STARFRAME_EMBED_V1_URL = "http://127.0.0.1:2236/v1"`
- `STARFRAME_CONTINUE_BRIDGE_URL = "http://127.0.0.1:11420"`
- `STARFRAME_MCP_CORE_URL = "http://127.0.0.1:8800"`
- `STARFRAME_MCP_UNIFIED_URL = "http://127.0.0.1:18789"`

## Current Expected Arbiter Chain

- `skill-hub`
- `request-loopback-resume`
- `skill-common-sense-engineering`
- `skill-enforcer`
- `usage-watcher`
- `skill-cost-credit-governor`
- `skill-cold-start-warm-path-optimizer`
- `skill-trust-ledger`
- `skill-auditor`
- `skill-arbiter-lockdown-admission`
