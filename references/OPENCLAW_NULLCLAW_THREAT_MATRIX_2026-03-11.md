# OpenClaw / NullClaw Threat Matrix

Date: 2026-03-11

Purpose: make third-party OpenClaw and NullClaw skill intake explicit, evidence-backed, and deny-by-default when provenance or behavior is risky.

## Public source matrix

| Surface | Evidence | Observed scale | Default risk | Why |
| --- | --- | ---: | --- | --- |
| `openclaw/skills` archived GitHub repo | `https://github.com/openclaw/skills` | `1000` top-level skill directories via GitHub contents API | `high` | Official archive shape helps provenance, but it still contains public third-party skill content and must be statically scanned before admission. |
| `openclaw/clawhub` / `clawhub.ai` | `https://github.com/openclaw/clawhub`, `https://clawhub.ai` | public registry / directory surface | `high` | Marketplace / registry discovery is not the same as trusted local admission. Searchable public skill directories widen supply-chain exposure. |
| `VoltAgent/awesome-openclaw-skills` | `https://github.com/VoltAgent/awesome-openclaw-skills` | claims `5400+` skills | `high` | Community mirror / aggregator. Large fan-out and secondary attribution make provenance weaker than the official archive. |
| `LeoYeAI/openclaw-master-skills` | `https://github.com/LeoYeAI/openclaw-master-skills` | claims `339+` skills | `high` | Curated community rollup sourced from ClawHub, GitHub, and community submissions. Multi-source aggregation increases ambiguity. |
| Public GitHub repos with `openclaw-skills` branding/topic | GitHub repository search | thousands of matching repositories | `high` | Direct repo installs bypass registry moderation and often mix code, binaries, docs, and automation. |
| `skills.sh/openclaw` and similar third-party registries | public web registry surface | independently unverified | `high` | Additional registry layer means additional trust boundary and potential package / mirror drift. |
| `nullclaw/nullclaw` official core repo | `https://github.com/nullclaw/nullclaw` | core product repo | `medium` | Official core repo is a better provenance anchor than random forks, but it is not a published skill registry. |
| Public GitHub repos advertising NullClaw skills / wrappers | GitHub repository search | fragmented third-party surface | `high` | No equivalent official NullClaw skill archive was surfaced. Provenance is therefore less clear by default. |
| npm packages pretending to install OpenClaw / NullClaw tooling | GhostLoader / fake installer campaign | live hostile campaign | `critical` | Fake installers can bypass repo provenance entirely and land persistence, credential theft, or RAT payloads. |

## Capability matrix

| Capability class | Default risk | Admission rule |
| --- | --- | --- |
| `npm` / `pnpm` / `npx` / `bunx` installer wrappers | `critical` | block |
| post-install / global PATH persistence | `critical` | block |
| fake password prompts / credential collection | `critical` | block |
| vendored `python.exe` / `pythonw.exe` or copied Python launchers | `critical` | block |
| hidden detached jobs (`pythonw`, `Start-Process -WindowStyle Hidden`, daemonized subprocesses) | `high` | block |
| broad process / port reaping (`Stop-Process -Force`, `taskkill /f`, blanket TCP kill logic) | `high` | block |
| browser auto-launch / unsolicited external UI opening | `high` | manual review or block |
| stale / hidden / untracked Python scripts | `high` or `critical` | block |
| wallet / seed phrase / trading / brokerage automation | `high` | manual review by default |
| shell / exec / deployment / SSH / remote tunnel surfaces | `high` | manual review by default |
| cross-agent tool or resource bridges paired with package execution | `critical` | block |

## Local diff-derived threat vectors that must stay guarded

These came directly from recent work across the local repos:

- hidden restart helpers and detached subprocess launch paths
- browser and web UI auto-launch behavior
- broad listener/process cleanup logic
- stale and untracked Python helper scripts
- copied or renamed Python launcher behavior
- cross-agent tool/resource surfaces spanning OpenClaw, NullClaw, MeshGPT, and local bridge lanes

## Operational policy

- Third-party OpenClaw / NullClaw skills are deny-by-default.
- Registry presence is not admission.
- A skill can only move from `blocked` to `manual_review` if it stops matching blocked supply-chain patterns.
- Any skill that combines remote package execution with agent tool/resource surfaces is treated as hostile until proven otherwise.
