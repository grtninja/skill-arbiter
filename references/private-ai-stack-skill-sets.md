# Private AI Stack Skill Sets

This reference maps the current private sister systems to explicit skill-arbiter portfolio lanes.

Each first-class sister system should have:

1. a dedicated operations skill for its owned worker/app/runtime
2. a validation or acceptance companion skill when startup/runtime state matters
3. shared cross-stack support lanes for orchestration, local-compute checks, and parallel work
4. an operator-language assist lane for UI labels, runbooks, handoff notes, and status translation

## `Private Media Workbench`

Dedicated system skills:

1. `media-workbench-desktop-ops`
2. `local-comfy-wan-multigpu`

Validation and support:

1. `desktop-startup-acceptance`
2. `heterogeneous-stack-validation`
3. `local-compute-usage`
4. `multitask-orchestrator`
5. `repo-b-mcp-comfy-bridge`
6. `repo-b-comfy-amuse-capcut-pipeline`

Gap candidates to keep explicit in the portfolio:

1. `media-workbench-worker-contracts`
2. `media-workbench-indexing-governance`

## `Private Training Workbench`

Dedicated system skills:

1. `qwen-training-workbench-ops`
2. `qwen-training-checkpoint-eval`
3. `qwen-training-desktop-ops`

Validation and support:

1. `desktop-startup-acceptance`
2. `heterogeneous-stack-validation`
3. `local-compute-usage`
4. `multitask-orchestrator`
5. `usage-watcher`

Gap candidates to keep explicit in the portfolio:

1. `qwen-training-campaign-ops`
2. `qwen-training-dataset-factory`

## `Private Avatar Host`

Dedicated system skills:

1. `repo-b-avatarcore-ops`
2. `desktop-startup-acceptance`

Validation and support:

1. `local-compute-usage`
2. `multitask-orchestrator`
3. `usage-watcher`

Gap candidates to keep explicit in the portfolio:

1. `avatarcore-desktop-acceptance`
2. `avatarcore-runtime-handoff-ops`

## `Private Speech Dashboard`

Dedicated system skills:

1. `desktop-startup-acceptance`
2. `local-compute-usage`

Validation and support:

1. `multitask-orchestrator`
2. `usage-watcher`

Gap candidates to keep explicit in the portfolio:

1. `shockwave-dashboard-ops`
2. `shockwave-operator-handoff`

## `Private VRM Local`

Dedicated system skills:

1. `vroid-template-asset-sync`
2. `blender-vrm-visible-fit`
3. `vroid-vrma-photobooth-pipeline`

Validation and support:

1. `local-compute-usage`
2. `multitask-orchestrator`
3. `usage-watcher`

Gap candidates to keep explicit in the portfolio:

1. `vrm-private-local-asset-staging`
2. `vroid-safe-ops-workflow`

## `Private Avatar Sandbox`

Dedicated system skills:

1. `repo-d-setup-diagnostics`
2. `repo-d-ui-guardrails`
3. `repo-d-local-packaging`
4. `vrm-material-lighting-debug`
5. `vrm-roundtrip-ci-gate`

Validation and support:

1. `desktop-startup-acceptance`
2. `local-compute-usage`
3. `multitask-orchestrator`
4. `usage-watcher`

Gap candidates to keep explicit in the portfolio:

1. `vrm-sandbox-startup-acceptance`
2. `vrm-sandbox-avatar-host-smoke`
3. `vrm-sandbox-audio-overlay-ops`

## `skill-arbiter`

Dedicated system skills:

1. `skill-arbiter-lockdown-admission`
2. `skill-auditor`
3. `skills-discovery-curation`
4. `skill-arbiter-release-ops`

Support skills:

1. `skill-enforcer`
2. `usage-watcher`
3. `skills-consolidation-architect`

## Cross-Stack Operator-Language Assist

`operator-language-humanizer` belongs in this portfolio as a cross-stack operator-language assist lane, not as a prose-only toy.

Its job is to:

1. translate raw worker, queue, model, and service state into operator-facing language
2. tighten UI labels, step text, and error summaries across desktop shells and local dashboards
3. rewrite machine-oriented notes into concise runbooks, handoff notes, and review prompts
4. support operator-facing language across Media Workbench, Qwen Training, AvatarCore, VRM surfaces, and Project Shockwave

It does not own ranking, trust, persona authority, or final system emission.

## Intake Rule

When a new sister system becomes a first-class local app or worker, it should ship with:

1. at least one dedicated operational skill
2. one validation or acceptance companion skill where appropriate
3. an explicit operator-language assist lane if operators read labels, steps, or runbook text
4. portfolio documentation in `recommended-skill-portfolio.md`
