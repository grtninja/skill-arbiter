# Complete Activated Skill Chain Workflow Audit

- Generated: `2026-03-05T11:45:12.937370Z`
- Activated skills audited: `146`
- Workflow chains generated: `18`
- Multitasking skill present: `True`
- Multitasking step used: `multitask-orchestrator`
- Uncovered skills: `0`

## Base Control Chain

1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skill-installer-plus`
8. `skill-auditor`
9. `skill-arbiter-lockdown-admission`
10. `skill-enforcer`

## Chain Workflows

### Apple/Mac Productivity Chain (`apple-mac-productivity`)

- Vendor: `Apple/macOS`
- Intent: Notes, reminders, tasks, and local messaging/productivity automation on macOS.
- Skills covered: `9`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `apple-notes`
8. `apple-reminders`
9. `bear-notes`
10. `bluebubbles`
11. `imsg`
12. `notion`
13. `obsidian`
14. `things-mac`
15. `trello`
16. `skill-installer-plus`
17. `skill-auditor`
18. `skill-arbiter-lockdown-admission`
19. `skill-enforcer`
- Covered skills:
  - `apple-notes`
  - `apple-reminders`
  - `bear-notes`
  - `bluebubbles`
  - `imsg`
  - `notion`
  - `obsidian`
  - `things-mac`
  - `trello`

### Browser + Design Automation Chain (`browser-design-automation`)

- Vendor: `Playwright/Figma`
- Intent: Cross-browser automation, screenshot evidence, and design-to-code implementation.
- Skills covered: `5`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `code-gap-sweeping`
8. `develop-web-game`
9. `figma`
10. `figma-implement-design`
11. `playwright-edge-preference`
12. `playwright-safe`
13. `skill-installer-plus`
14. `skill-auditor`
15. `skill-arbiter-lockdown-admission`
16. `skill-enforcer`
- Covered skills:
  - `develop-web-game`
  - `figma`
  - `figma-implement-design`
  - `playwright-edge-preference`
  - `playwright-safe`

### Collaboration Communication Chain (`collab-communication`)

- Vendor: `Slack/Discord/Feishu`
- Intent: Team communication and collaborative docs/drive permission workflows.
- Skills covered: `6`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `docs-alignment-lock`
8. `discord`
9. `feishu-doc`
10. `feishu-drive`
11. `feishu-perm`
12. `feishu-wiki`
13. `slack`
14. `skill-installer-plus`
15. `skill-auditor`
16. `skill-arbiter-lockdown-admission`
17. `skill-enforcer`
- Covered skills:
  - `discord`
  - `feishu-doc`
  - `feishu-drive`
  - `feishu-perm`
  - `feishu-wiki`
  - `slack`

### Docs + Data Asset Chain (`docs-data-assets`)

- Vendor: `Productivity`
- Intent: Structured document, PDF, spreadsheet, and notebook workflows.
- Skills covered: `3`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `jupyter-notebook`
8. `pdf`
9. `spreadsheet`
10. `skill-installer-plus`
11. `skill-auditor`
12. `skill-arbiter-lockdown-admission`
13. `skill-enforcer`
- Covered skills:
  - `jupyter-notebook`
  - `pdf`
  - `spreadsheet`

### GitHub DevOps Chain (`github-devops`)

- Vendor: `GitHub`
- Intent: Issue/PR triage, CI remediation, and comment resolution using GitHub tooling.
- Skills covered: `4`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `session-logs`
8. `healthcheck`
9. `coding-agent`
10. `diffs`
11. `gh-issues`
12. `github`
13. `skill-installer-plus`
14. `skill-auditor`
15. `skill-arbiter-lockdown-admission`
16. `skill-enforcer`
- Covered skills:
  - `coding-agent`
  - `diffs`
  - `gh-issues`
  - `github`

### Governance Core Chain (`governance-core`)

- Vendor: `internal`
- Intent: Route, budget, audit, admission, and policy alignment for all skill-driven work.
- Skills covered: `28`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skills-cross-repo-radar`
8. `code-gap-sweeping`
9. `request-loopback-resume`
10. `docs-alignment-lock`
11. `local-compute-usage`
12. `playwright-edge-preference`
13. `playwright-safe`
14. `safe-mass-index-core`
15. `skill-arbiter`
16. `skill-arbiter-churn-forensics`
17. `skill-arbiter-lockdown-admission`
18. `skill-arbiter-release-ops`
19. `skill-auditor`
20. `skill-blast-radius-simulator`
21. `skill-creator-openclaw`
22. `skill-dependency-fan-out-inspector`
23. `skill-enforcer`
24. `skill-installer-plus`
25. `skill-trust-ledger`
26. `skills-consolidation-architect`
27. `skills-discovery-curation`
28. `skills-third-party-intake`
- Covered skills:
  - `code-gap-sweeping`
  - `docs-alignment-lock`
  - `local-compute-usage`
  - `multitask-orchestrator`
  - `playwright-edge-preference`
  - `playwright-safe`
  - `request-loopback-resume`
  - `safe-mass-index-core`
  - `skill-arbiter`
  - `skill-arbiter-churn-forensics`
  - `skill-arbiter-lockdown-admission`
  - `skill-arbiter-release-ops`
  - `skill-auditor`
  - `skill-blast-radius-simulator`
  - `skill-cold-start-warm-path-optimizer`
  - `skill-common-sense-engineering`
  - `skill-cost-credit-governor`
  - `skill-creator-openclaw`
  - `skill-dependency-fan-out-inspector`
  - `skill-enforcer`
  - `skill-hub`
  - `skill-installer-plus`
  - `skill-trust-ledger`
  - `skills-consolidation-architect`
  - `skills-cross-repo-radar`
  - `skills-discovery-curation`
  - `skills-third-party-intake`
  - `usage-watcher`

### Microsoft Native App Chain (`microsoft-native-apps`)

- Vendor: `Microsoft/.NET`
- Intent: Native .NET and desktop app build scaffolding/workflow chaining.
- Skills covered: `2`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `code-gap-sweeping`
8. `aspnet-core`
9. `winui-app`
10. `skill-installer-plus`
11. `skill-auditor`
12. `skill-arbiter-lockdown-admission`
13. `skill-enforcer`
- Covered skills:
  - `aspnet-core`
  - `winui-app`

### Notion + Linear PM Chain (`notion-linear-pm`)

- Vendor: `Notion/Linear`
- Intent: Planning, knowledge capture, and issue workflow orchestration.
- Skills covered: `6`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `docs-alignment-lock`
8. `linear`
9. `notion`
10. `notion-knowledge-capture`
11. `notion-meeting-intelligence`
12. `notion-research-documentation`
13. `notion-spec-to-implementation`
14. `skill-installer-plus`
15. `skill-auditor`
16. `skill-arbiter-lockdown-admission`
17. `skill-enforcer`
- Covered skills:
  - `linear`
  - `notion`
  - `notion-knowledge-capture`
  - `notion-meeting-intelligence`
  - `notion-research-documentation`
  - `notion-spec-to-implementation`

### OpenAI Media AI Chain (`openai-media-ai`)

- Vendor: `OpenAI`
- Intent: Image, audio, video, speech, and transcript generation workflows.
- Skills covered: `12`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `openai-docs`
8. `imagegen`
9. `model-usage`
10. `nano-banana-pro`
11. `openai-image-gen`
12. `openai-whisper`
13. `openai-whisper-api`
14. `sherpa-onnx-tts`
15. `songsee`
16. `sora`
17. `speech`
18. `transcribe`
19. `video-frames`
20. `skill-installer-plus`
21. `skill-auditor`
22. `skill-arbiter-lockdown-admission`
23. `skill-enforcer`
- Covered skills:
  - `imagegen`
  - `model-usage`
  - `nano-banana-pro`
  - `openai-image-gen`
  - `openai-whisper`
  - `openai-whisper-api`
  - `sherpa-onnx-tts`
  - `songsee`
  - `sora`
  - `speech`
  - `transcribe`
  - `video-frames`

### OpenClaw ACP Vendor Chain (`openclaw-acp-vendor`)

- Vendor: `OpenClaw/ACP`
- Intent: Vendor-specific ACP routing, utility toolchains, and command-lane orchestration.
- Skills covered: `32`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `1password`
8. `acp-router`
9. `blogwatcher`
10. `blucli`
11. `camsnap`
12. `canvas`
13. `clawhub`
14. `eightctl`
15. `gemini`
16. `gifgrep`
17. `gog`
18. `goplaces`
19. `healthcheck`
20. `himalaya`
21. `lobster`
22. `mcporter`
23. `nano-pdf`
24. `openhue`
25. `oracle`
26. `ordercli`
27. `peekaboo`
28. `prose`
29. `sag`
30. `session-logs`
31. `sonoscli`
32. `spotify-player`
33. `summarize`
34. `tmux`
35. `voice-call`
36. `wacli`
37. `weather`
38. `xurl`
39. `skill-installer-plus`
40. `skill-auditor`
41. `skill-arbiter-lockdown-admission`
42. `skill-enforcer`
- Covered skills:
  - `1password`
  - `acp-router`
  - `blogwatcher`
  - `blucli`
  - `camsnap`
  - `canvas`
  - `clawhub`
  - `eightctl`
  - `gemini`
  - `gifgrep`
  - `gog`
  - `goplaces`
  - `healthcheck`
  - `himalaya`
  - `lobster`
  - `mcporter`
  - `nano-pdf`
  - `openhue`
  - `oracle`
  - `ordercli`
  - `peekaboo`
  - `prose`
  - `sag`
  - `session-logs`
  - `sonoscli`
  - `spotify-player`
  - `summarize`
  - `tmux`
  - `voice-call`
  - `wacli`
  - `weather`
  - `xurl`

### Repo A DDC Chain (`repo-a-ddc`)

- Vendor: `<PRIVATE_REPO_A>`
- Intent: Coordinator smoke, policy self-test, and telemetry/KV guard execution for Repo A lanes.
- Skills covered: `3`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skills-cross-repo-radar`
8. `code-gap-sweeping`
9. `request-loopback-resume`
10. `repo-a-coordinator-smoke`
11. `repo-a-policy-selftest-gate`
12. `repo-a-telemetry-kv-guard`
13. `skill-installer-plus`
14. `skill-auditor`
15. `skill-arbiter-lockdown-admission`
16. `skill-enforcer`
- Covered skills:
  - `repo-a-coordinator-smoke`
  - `repo-a-policy-selftest-gate`
  - `repo-a-telemetry-kv-guard`

### Repo B Operations Chain (`repo-b-ops`)

- Vendor: `<PRIVATE_REPO_B>`
- Intent: Control center, bridge, routing, and Comfy orchestration workflows for Repo B.
- Skills covered: `13`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skills-cross-repo-radar`
8. `code-gap-sweeping`
9. `request-loopback-resume`
10. `repo-b-agent-bridge-safety`
11. `repo-b-avatarcore-ops`
12. `repo-b-comfy-amuse-capcut-pipeline`
13. `repo-b-control-center-ops`
14. `repo-b-hardware-first`
15. `repo-b-local-bridge-orchestrator`
16. `repo-b-local-comfy-orchestrator`
17. `repo-b-mass-index-ops`
18. `repo-b-mcp-comfy-bridge`
19. `repo-b-preflight-doc-sync`
20. `repo-b-starframe-ops`
21. `repo-b-thin-waist-routing`
22. `repo-b-wsl-hybrid-ops`
23. `skill-installer-plus`
24. `skill-auditor`
25. `skill-arbiter-lockdown-admission`
26. `skill-enforcer`
- Covered skills:
  - `repo-b-agent-bridge-safety`
  - `repo-b-avatarcore-ops`
  - `repo-b-comfy-amuse-capcut-pipeline`
  - `repo-b-control-center-ops`
  - `repo-b-hardware-first`
  - `repo-b-local-bridge-orchestrator`
  - `repo-b-local-comfy-orchestrator`
  - `repo-b-mass-index-ops`
  - `repo-b-mcp-comfy-bridge`
  - `repo-b-preflight-doc-sync`
  - `repo-b-starframe-ops`
  - `repo-b-thin-waist-routing`
  - `repo-b-wsl-hybrid-ops`

### Repo C Governance Chain (`repo-c-governance`)

- Vendor: `<PRIVATE_REPO_C>`
- Intent: Policy schema, ranking contracts, trace validation, and persona registry maintenance.
- Skills covered: `7`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skills-cross-repo-radar`
8. `code-gap-sweeping`
9. `request-loopback-resume`
10. `repo-c-boundary-governance`
11. `repo-c-mass-index-ops`
12. `repo-c-persona-registry-maintenance`
13. `repo-c-policy-schema-gate`
14. `repo-c-ranking-contracts`
15. `repo-c-shim-contract-checks`
16. `repo-c-trace-ndjson-validate`
17. `skill-installer-plus`
18. `skill-auditor`
19. `skill-arbiter-lockdown-admission`
20. `skill-enforcer`
- Covered skills:
  - `repo-c-boundary-governance`
  - `repo-c-mass-index-ops`
  - `repo-c-persona-registry-maintenance`
  - `repo-c-policy-schema-gate`
  - `repo-c-ranking-contracts`
  - `repo-c-shim-contract-checks`
  - `repo-c-trace-ndjson-validate`

### Repo D UI Packaging Chain (`repo-d-packaging`)

- Vendor: `<PRIVATE_REPO_D>`
- Intent: Desktop setup, UI guardrails, mass index, and local packaging validation for Repo D.
- Skills covered: `4`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skills-cross-repo-radar`
8. `code-gap-sweeping`
9. `request-loopback-resume`
10. `repo-d-local-packaging`
11. `repo-d-mass-index-ops`
12. `repo-d-setup-diagnostics`
13. `repo-d-ui-guardrails`
14. `skill-installer-plus`
15. `skill-auditor`
16. `skill-arbiter-lockdown-admission`
17. `skill-enforcer`
- Covered skills:
  - `repo-d-local-packaging`
  - `repo-d-mass-index-ops`
  - `repo-d-setup-diagnostics`
  - `repo-d-ui-guardrails`

### Security Assurance Chain (`security-assurance`)

- Vendor: `Security`
- Intent: Security best-practice review, threat modeling, and ownership-risk mapping.
- Skills covered: `3`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skill-enforcer`
8. `security-best-practices`
9. `security-ownership-map`
10. `sentry`
11. `skill-installer-plus`
12. `skill-auditor`
13. `skill-arbiter-lockdown-admission`
- Covered skills:
  - `security-best-practices`
  - `security-ownership-map`
  - `sentry`

### General Utility Chain (`utility-general`)

- Vendor: `Mixed`
- Intent: Catch-all fallback for utility skills without a strong vendor lane.
- Skills covered: `3`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `chatgpt-apps`
8. `openai-docs`
9. `yeet`
10. `skill-installer-plus`
11. `skill-auditor`
12. `skill-arbiter-lockdown-admission`
13. `skill-enforcer`
- Covered skills:
  - `chatgpt-apps`
  - `openai-docs`
  - `yeet`

### VRM Avatar Pipeline Chain (`vrm-avatar-pipeline`)

- Vendor: `Blender/VRM`
- Intent: Template normalization, visible fit, animation export, and roundtrip quality gates.
- Skills covered: `5`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `blender-vrm-avatar-ops`
8. `blender-vrm-visible-fit`
9. `vrm-roundtrip-ci-gate`
10. `vroid-template-asset-sync`
11. `vroid-vrma-photobooth-pipeline`
12. `skill-installer-plus`
13. `skill-auditor`
14. `skill-arbiter-lockdown-admission`
15. `skill-enforcer`
- Covered skills:
  - `blender-vrm-avatar-ops`
  - `blender-vrm-visible-fit`
  - `vrm-roundtrip-ci-gate`
  - `vroid-template-asset-sync`
  - `vroid-vrma-photobooth-pipeline`

### Web Deployment Vendor Chain (`web-deploy-vendors`)

- Vendor: `Cloudflare/Netlify/Render/Vercel`
- Intent: Deploy web projects with vendor-specific CLI pathways and deterministic release checks.
- Skills covered: `4`
- Steps:
1. `skill-hub`
2. `multitask-orchestrator`
3. `skill-common-sense-engineering`
4. `usage-watcher`
5. `skill-cost-credit-governor`
6. `skill-cold-start-warm-path-optimizer`
7. `skill-arbiter-release-ops`
8. `cloudflare-deploy`
9. `netlify-deploy`
10. `render-deploy`
11. `vercel-deploy`
12. `skill-installer-plus`
13. `skill-auditor`
14. `skill-arbiter-lockdown-admission`
15. `skill-enforcer`
- Covered skills:
  - `cloudflare-deploy`
  - `netlify-deploy`
  - `render-deploy`
  - `vercel-deploy`

## Per-Skill Chain Coverage

| Skill | Source | Chains |
| --- | --- | --- |
| `1password` | `top-level` | `openclaw-acp-vendor` |
| `acp-router` | `top-level` | `openclaw-acp-vendor` |
| `apple-notes` | `top-level` | `apple-mac-productivity` |
| `apple-reminders` | `top-level` | `apple-mac-productivity` |
| `aspnet-core` | `top-level` | `microsoft-native-apps` |
| `bear-notes` | `top-level` | `apple-mac-productivity` |
| `blender-vrm-avatar-ops` | `top-level` | `vrm-avatar-pipeline` |
| `blender-vrm-visible-fit` | `top-level` | `vrm-avatar-pipeline` |
| `blogwatcher` | `top-level` | `openclaw-acp-vendor` |
| `blucli` | `top-level` | `openclaw-acp-vendor` |
| `bluebubbles` | `top-level` | `apple-mac-productivity` |
| `camsnap` | `top-level` | `openclaw-acp-vendor` |
| `canvas` | `top-level` | `openclaw-acp-vendor` |
| `chatgpt-apps` | `top-level` | `utility-general` |
| `clawhub` | `top-level` | `openclaw-acp-vendor` |
| `cloudflare-deploy` | `top-level` | `web-deploy-vendors` |
| `code-gap-sweeping` | `top-level` | `governance-core` |
| `coding-agent` | `top-level` | `github-devops` |
| `develop-web-game` | `top-level` | `browser-design-automation` |
| `diffs` | `top-level` | `github-devops` |
| `discord` | `top-level` | `collab-communication` |
| `docs-alignment-lock` | `top-level` | `governance-core` |
| `eightctl` | `top-level` | `openclaw-acp-vendor` |
| `feishu-doc` | `top-level` | `collab-communication` |
| `feishu-drive` | `top-level` | `collab-communication` |
| `feishu-perm` | `top-level` | `collab-communication` |
| `feishu-wiki` | `top-level` | `collab-communication` |
| `figma` | `top-level` | `browser-design-automation` |
| `figma-implement-design` | `top-level` | `browser-design-automation` |
| `gemini` | `top-level` | `openclaw-acp-vendor` |
| `gh-issues` | `top-level` | `github-devops` |
| `gifgrep` | `top-level` | `openclaw-acp-vendor` |
| `github` | `top-level` | `github-devops` |
| `gog` | `top-level` | `openclaw-acp-vendor` |
| `goplaces` | `top-level` | `openclaw-acp-vendor` |
| `healthcheck` | `top-level` | `openclaw-acp-vendor` |
| `himalaya` | `top-level` | `openclaw-acp-vendor` |
| `imagegen` | `top-level` | `openai-media-ai` |
| `imsg` | `top-level` | `apple-mac-productivity` |
| `jupyter-notebook` | `top-level` | `docs-data-assets` |
| `linear` | `top-level` | `notion-linear-pm` |
| `lobster` | `top-level` | `openclaw-acp-vendor` |
| `local-compute-usage` | `top-level` | `governance-core` |
| `mcporter` | `top-level` | `openclaw-acp-vendor` |
| `model-usage` | `top-level` | `openai-media-ai` |
| `multitask-orchestrator` | `top-level` | `governance-core` |
| `nano-banana-pro` | `top-level` | `openai-media-ai` |
| `nano-pdf` | `top-level` | `openclaw-acp-vendor` |
| `netlify-deploy` | `top-level` | `web-deploy-vendors` |
| `notion` | `top-level` | `apple-mac-productivity`, `notion-linear-pm` |
| `notion-knowledge-capture` | `top-level` | `notion-linear-pm` |
| `notion-meeting-intelligence` | `top-level` | `notion-linear-pm` |
| `notion-research-documentation` | `top-level` | `notion-linear-pm` |
| `notion-spec-to-implementation` | `top-level` | `notion-linear-pm` |
| `obsidian` | `top-level` | `apple-mac-productivity` |
| `openai-docs` | `top-level` | `utility-general` |
| `openai-image-gen` | `top-level` | `openai-media-ai` |
| `openai-whisper` | `top-level` | `openai-media-ai` |
| `openai-whisper-api` | `top-level` | `openai-media-ai` |
| `openhue` | `top-level` | `openclaw-acp-vendor` |
| `oracle` | `top-level` | `openclaw-acp-vendor` |
| `ordercli` | `top-level` | `openclaw-acp-vendor` |
| `pdf` | `top-level` | `docs-data-assets` |
| `peekaboo` | `top-level` | `openclaw-acp-vendor` |
| `playwright-edge-preference` | `top-level` | `browser-design-automation`, `governance-core` |
| `playwright-safe` | `top-level` | `browser-design-automation`, `governance-core` |
| `prose` | `top-level` | `openclaw-acp-vendor` |
| `render-deploy` | `top-level` | `web-deploy-vendors` |
| `repo-a-coordinator-smoke` | `top-level` | `repo-a-ddc` |
| `repo-a-policy-selftest-gate` | `top-level` | `repo-a-ddc` |
| `repo-a-telemetry-kv-guard` | `top-level` | `repo-a-ddc` |
| `repo-b-agent-bridge-safety` | `top-level` | `repo-b-ops` |
| `repo-b-avatarcore-ops` | `top-level` | `repo-b-ops` |
| `repo-b-comfy-amuse-capcut-pipeline` | `top-level` | `repo-b-ops` |
| `repo-b-control-center-ops` | `top-level` | `repo-b-ops` |
| `repo-b-hardware-first` | `top-level` | `repo-b-ops` |
| `repo-b-local-bridge-orchestrator` | `top-level` | `repo-b-ops` |
| `repo-b-local-comfy-orchestrator` | `top-level` | `repo-b-ops` |
| `repo-b-mass-index-ops` | `top-level` | `repo-b-ops` |
| `repo-b-mcp-comfy-bridge` | `top-level` | `repo-b-ops` |
| `repo-b-preflight-doc-sync` | `top-level` | `repo-b-ops` |
| `repo-b-starframe-ops` | `top-level` | `repo-b-ops` |
| `repo-b-thin-waist-routing` | `top-level` | `repo-b-ops` |
| `repo-b-wsl-hybrid-ops` | `top-level` | `repo-b-ops` |
| `repo-c-boundary-governance` | `top-level` | `repo-c-governance` |
| `repo-c-mass-index-ops` | `top-level` | `repo-c-governance` |
| `repo-c-persona-registry-maintenance` | `top-level` | `repo-c-governance` |
| `repo-c-policy-schema-gate` | `top-level` | `repo-c-governance` |
| `repo-c-ranking-contracts` | `top-level` | `repo-c-governance` |
| `repo-c-shim-contract-checks` | `top-level` | `repo-c-governance` |
| `repo-c-trace-ndjson-validate` | `top-level` | `repo-c-governance` |
| `repo-d-local-packaging` | `top-level` | `repo-d-packaging` |
| `repo-d-mass-index-ops` | `top-level` | `repo-d-packaging` |
| `repo-d-setup-diagnostics` | `top-level` | `repo-d-packaging` |
| `repo-d-ui-guardrails` | `top-level` | `repo-d-packaging` |
| `request-loopback-resume` | `top-level` | `governance-core` |
| `safe-mass-index-core` | `top-level` | `governance-core` |
| `sag` | `top-level` | `openclaw-acp-vendor` |
| `security-best-practices` | `top-level` | `security-assurance` |
| `security-ownership-map` | `top-level` | `security-assurance` |
| `sentry` | `top-level` | `security-assurance` |
| `session-logs` | `top-level` | `openclaw-acp-vendor` |
| `sherpa-onnx-tts` | `top-level` | `openai-media-ai` |
| `skill-arbiter` | `top-level` | `governance-core` |
| `skill-arbiter-churn-forensics` | `top-level` | `governance-core` |
| `skill-arbiter-lockdown-admission` | `top-level` | `governance-core` |
| `skill-arbiter-release-ops` | `top-level` | `governance-core` |
| `skill-auditor` | `top-level` | `governance-core` |
| `skill-blast-radius-simulator` | `top-level` | `governance-core` |
| `skill-cold-start-warm-path-optimizer` | `top-level` | `governance-core` |
| `skill-common-sense-engineering` | `top-level` | `governance-core` |
| `skill-cost-credit-governor` | `top-level` | `governance-core` |
| `skill-creator-openclaw` | `top-level` | `governance-core` |
| `skill-dependency-fan-out-inspector` | `top-level` | `governance-core` |
| `skill-enforcer` | `top-level` | `governance-core` |
| `skill-hub` | `top-level` | `governance-core` |
| `skill-installer-plus` | `top-level` | `governance-core` |
| `skill-trust-ledger` | `top-level` | `governance-core` |
| `skills-consolidation-architect` | `top-level` | `governance-core` |
| `skills-cross-repo-radar` | `top-level` | `governance-core` |
| `skills-discovery-curation` | `top-level` | `governance-core` |
| `skills-third-party-intake` | `top-level` | `governance-core` |
| `slack` | `top-level` | `collab-communication` |
| `songsee` | `top-level` | `openai-media-ai` |
| `sonoscli` | `top-level` | `openclaw-acp-vendor` |
| `sora` | `top-level` | `openai-media-ai` |
| `speech` | `top-level` | `openai-media-ai` |
| `spotify-player` | `top-level` | `openclaw-acp-vendor` |
| `spreadsheet` | `top-level` | `docs-data-assets` |
| `summarize` | `top-level` | `openclaw-acp-vendor` |
| `things-mac` | `top-level` | `apple-mac-productivity` |
| `tmux` | `top-level` | `openclaw-acp-vendor` |
| `transcribe` | `top-level` | `openai-media-ai` |
| `trello` | `top-level` | `apple-mac-productivity` |
| `usage-watcher` | `top-level` | `governance-core` |
| `vercel-deploy` | `top-level` | `web-deploy-vendors` |
| `video-frames` | `top-level` | `openai-media-ai` |
| `voice-call` | `top-level` | `openclaw-acp-vendor` |
| `vrm-roundtrip-ci-gate` | `top-level` | `vrm-avatar-pipeline` |
| `vroid-template-asset-sync` | `top-level` | `vrm-avatar-pipeline` |
| `vroid-vrma-photobooth-pipeline` | `top-level` | `vrm-avatar-pipeline` |
| `wacli` | `top-level` | `openclaw-acp-vendor` |
| `weather` | `top-level` | `openclaw-acp-vendor` |
| `winui-app` | `top-level` | `microsoft-native-apps` |
| `xurl` | `top-level` | `openclaw-acp-vendor` |
| `yeet` | `top-level` | `utility-general` |

## Multitasking Policy

- `multitask-orchestrator` is installed and should be used after `skill-hub` for 2+ independent lanes.
