---
name: codex-config-self-maintenance
description: Safely maintain Codex config.toml and repo-backed Codex machine profiles using a candidate-first workflow with temp-file TOML validation, active-vs-commented MCP checks, exact insertion-point reporting, and stack-aware parity checks. Use when updating ~/.codex/config.toml, adding or fixing MCP servers, reasoning visibility, skill-arbiter bindings, trusted project entries, per-machine Codex profiles, or when the Codex settings UI does not match the expected MCP/runtime contract.
---

# Codex Config Self Maintenance

Use this skill to keep Codex configuration changes safe, explicit, and aligned with the live STARFRAME stack.

## Workflow

1. Read the live target config once.
2. Decide whether the change belongs in:
   - `%USERPROFILE%\.codex\config.toml`
   - a repo-backed profile under `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles`
3. Build a temp candidate instead of writing the live file first.
4. Validate the candidate with `scripts/validate_candidate.py`.
5. Use `$dated-version-tracking` to record any version, dependency, or prior-context assumption that affects the config.
6. For current/latest model, MCP startup, sandbox, VS Code settings, profile, or sync behavior, verify against official docs before changing durable defaults.
7. Before promotion, catalog `.codex\config.stale` in dry-run mode so stale backups and failed configs are classified, not left loose in `.codex`.
8. Compare active MCP tables against commented examples so UI discrepancies are explained by real active config, not assumptions.
9. Report exact insertion points or provide a full candidate file path before any live replacement.
10. Only write the live file when the operator explicitly wants the replacement applied.
11. After promotion, snapshot the new live config into `config.stale\Current Config`, move old config backups/failures into `config.stale`, and re-run validation.

## Candidate-first Protocol

- Treat `config.toml` as fragile.
- Treat all config, sandbox, and profile files as read-only by default until the explicit preflight gates below pass.
- Do not directly patch the live file when a temp candidate plus manual replacement is safer.
- Prefer a temp candidate under `%USERPROFILE%\AppData\Local\Temp`.
- Keep the live file untouched until the candidate is parse-green and the targeted assertions pass.
- Keep root `.codex` clean by using `%USERPROFILE%\.codex\config.stale` as the dated evidence lane for old backups, failed configs, and broken config artifacts.
- For manual replacement workflows, hand the operator:
  - the candidate file path,
  - exact insertion or replacement points,
  - the validated keys or MCP server list.

## Config.stale Workflow

`%USERPROFILE%\.codex\config.stale` is part of the safe config update workflow.

Bucket contract:

- `Current Config`: copied live snapshots for comparison only.
- `Past Good Configs`: parseable historical configs. They may be useful evidence, but they are stale until revalidated.
- `Broken Configs`: failed, malformed, forbidden, or known-bad configs retained as regression evidence.

Before any live config promotion:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\inventory_codex_home.py --write
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --dry-run --require-preflight
```

After any live config promotion or rollback repair:

```powershell
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\catalog_config_stale.py --organize --include-broken-artifacts --require-preflight
python %USERPROFILE%\.codex\skills\dated-version-tracking\scripts\dated_context_ledger.py validate
```

Do not move active runtime state during cleanup:

- `auth.json`
- `config.toml`
- `state_*.sqlite*`
- `logs_*.sqlite`
- `*.sqlite-wal`
- `*.sqlite-shm`
- `sessions`
- `logs`
- `.sandbox`

Moving `.sandbox.broken`, `*.broken`, and `config.toml.fail*` into `Broken Configs` is allowed because those are explicitly non-live evidence artifacts.

## Read-only Preflight Gates

Before any write, move, or promotion involving config, sandbox, or VS Code profile/settings files:

1. Write a root inventory with `inventory_codex_home.py --write`.
2. Run the intended operation in dry-run mode.
3. Prove live `config.toml` still parses and has `model = "gpt-5.5"`, `review_model = "gpt-5.5"`, `model_reasoning_effort = "xhigh"`, `profile = "starframe"`, `features.shell_snapshot = false`, no required MCP servers, and no forbidden provider override.
4. Confirm the operation excludes `auth.json`, live `config.toml`, active SQLite/WAL/SHM files, sessions, logs, and current `.sandbox`.
5. Record the dated assumption or context request in the dated-version ledger.
6. For VS Code profile/settings files, back up the exact file, write a candidate, validate JSON, then promote.
7. For sandbox cleanup, only `.sandbox.broken` may move automatically; current `.sandbox` is read-only unless Eddie explicitly authorizes a sandbox reset.

## Process Cleanup Doctrine

- When the config change affects runtime cleanup, compaction behavior, or report hygiene, wire the stale-process rule directly into the candidate instructions instead of leaving it implied.
- The config guidance must require a stale-process sweep:
  - after every compaction
  - before every report
- The config guidance must use an explicit culprit map with four buckets:
  - `keep`
  - `kill`
  - `suspect-but-verify`
  - `exclude`
- For `SOUNDWAVE3`, the protected keep set must explicitly cover:
  - listener owners and direct parents for `1234`, `2236`, `2337`, `8787`, `8890`, `9000`, `11420`, and `18789`
  - the active PC Control supervisor tree:
    - `run_pc_supervisor.py`
    - `run_hub.py`
    - `run_input_bridge.py`
    - `run_voice_bridge.py`
    - `run_edge_chatgpt_bridge.py`
    - `launchDesktop.cjs`
    - `StarframePCSupervisor.exe`
    - `StarframePCHub.exe`
    - `StarframePCInputBridge.exe`
    - `StarframePCVoiceBridge.exe`
    - `StarframePCEdgeChatGPTBridge.exe`
    - `mx3-shim-server.exe`
    - `mx3-pose-server.exe`
    - `mx3-bridge-server.exe`
    - `starframe-unified.exe`
- The kill set must only include orphaned wrappers or stale helpers such as:
  - `continue_mcp_stdio_bridge_entry.py`
  - `switch_mx3_dfp_runtime.py`
  - `restart_local_apps.py`
  - `start_full_apps.py`
  - orphaned `rg.exe`, temporary `pwsh.exe`, or `cmd.exe` wrappers that do not own or parent live listeners
  - raw long-lived `python.exe` / `pythonw.exe` app-stack owners when a repo-owned named launcher equivalent exists
- The suspect-but-verify set must map long-lived helpers explicitly before acting, including:
  - `nullclaw_agent.py`
  - long-lived Codex parser `pwsh.exe`
  - non-listener `python.exe` / `node.exe` processes older than 10 minutes when they are not named-launcher drift
- The exclude set must protect unrelated operator/system surfaces by default, including:
  - `LEDKeeper2`
  - `MSIAfterburner`
  - `RadeonSoftware`
  - `cncmd.exe`
  - `AMDRSServ.exe` wrappers
  - `explorer.exe`
  - `ChatGPT.exe` / `LM Studio.exe` style user-facing desktop apps unless Eddie explicitly asks for them to be touched

## Required Checks

Run the validator after changing a candidate:

```powershell
python <PRIVATE_REPO_ROOT>\skill-candidates\codex-config-self-maintenance\scripts\validate_candidate.py `
  %USERPROFILE%\AppData\Local\Temp\codex_config_candidate.toml `
  --require-mcp starframe-local-mcp `
  --require-model gpt-5.5 `
  --require-reasoning xhigh
```

For the current STARFRAME main-lane contract, also require:

- `codex-local`
- `openaiDeveloperDocs`

when the goal is parity with the Codex settings MCP panel.

## MCP Discrepancy Rule

If the Codex settings UI shows fewer MCP servers than expected:

1. Inspect active `[mcp_servers.*]` tables in the live file.
2. Check whether the “missing” servers exist only as commented examples.
3. Check for stale schema shapes in comments or candidates.
4. Do not claim a server is loaded unless it is in an active TOML table and the candidate parses.

## Stack-specific Contract

- Main model: `gpt-5.5`
- Main reasoning: `xhigh`
- Dated model assumption: GPT-5.5 was user-reported as released on 2026-04-23 and official OpenAI docs verified on 2026-04-24 that GPT-5.5 is current for ChatGPT and Codex. Any active 5.4-as-latest/default/main-lane claim after 2026-04-23 is stale unless explicitly historical.
- Public authority plane: `http://127.0.0.1:9000/v1`
- Hosted main lane: `http://127.0.0.1:2337/v1`
- Standalone embed lane: `http://127.0.0.1:2236/v1`
- Continue bridge: `http://127.0.0.1:11420`
- PC Control core: `http://127.0.0.1:8800`
- Unified broker: `http://127.0.0.1:18789`
- Mandatory skill router chain:
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

## Machine-profile Rule

When the request is about propagation or parity across machines, update the repo-backed machine profiles instead of only the local live config:

- `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\this_machine.toml`
- `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\cybertron_core.toml`
- `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\shockwaveitx.toml`
- `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\template.toml`
- `G:\GitHub\<PRIVATE_REPO_A>\config\codex_profiles\profiles.json`

## References

- `<PRIVATE_REPO_ROOT>\references\codex-config-self-maintenance.md`
- `references/config-contract.md`
- `references/manifest-evidence.md`
- `scripts/validate_candidate.py`
- `%USERPROFILE%\.codex\skills\dated-version-tracking\references\online-grounding.md`

## Loopback

If the candidate fails validation:

1. Capture the exact failing key or TOML parse error.
2. Fix the candidate, not the live file.
3. Re-run validation until the candidate is green.
4. Only then proceed to operator handoff or live replacement.
