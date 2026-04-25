---
name: "white-hat"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Run a defender-first security sweep on code, configs, prompts, model/tooling surfaces, or third-party contribution lanes. Use when a request involves safe bug, leak, zero-day-class, exploit, or hack hunting for protection, when contributing to outside repositories and you want a focused security pass, or when touching auth, secrets, permissions, network exposure, prompt/tool boundaries, data flow, or update/build surfaces. This skill is defensive only and must never be used for weaponization or unauthorized access."
---

# White Hat

## Overview

Use this skill to keep technical work on the good-guy side: proactively look for bugs, leaks, unsafe defaults, exploitable states, and disclosure obligations without turning the task into offensive security work. Apply it before and after meaningful edits on sensitive surfaces and whenever the user explicitly asks for a safety, leak, exploit, vulnerability, or hardening sweep.

## When to use

- The user explicitly asks for a security sweep, white-hat review, leak hunt, exploit hunt for defense, zero-day-class review, or third-party contribution hardening.
- The task touches auth, sessions, permissions, secrets, prompt/tool boundaries, model context handling, file/network exposure, build or update pipelines, parsers, or dependency execution.
- The task touches `.github/workflows/**`, GitHub rulesets, CODEOWNERS, protected branches, `GITHUB_TOKEN` permissions, reusable workflows, or CI/CD secret handling.
- You are preparing a contribution to a third-party repository and need to avoid shipping a latent vulnerability.

## Quest-Grade Third-Party Lane

When the job is third-party bug hunting or contribution hardening, route through the smallest deterministic chain instead of improvising the whole flow each time.

Recommended chain:

`$skill-hub` -> `$request-loopback-resume` -> `$third-party-pr-radar` -> `$white-hat` -> `$github` -> `$skill-common-sense-engineering` -> `$skill-enforcer`

Add follow-on skills only when the lane actually needs them:

- `$gh-address-comments` for current-head PR review feedback
- `$gh-fix-ci` for active GitHub Actions failures on the current head

Minimum checkpoints for that lane:

- open issues and open PRs rechecked so the patch does not duplicate live work
- current head SHA captured before reacting to CI or bot feedback
- repo-native validation lanes mapped before running local proof
- smallest safe proof captured for any confirmed issue
- post-edit white-hat recheck completed before submission or PR follow-up

## Best-Fit Companion Skills

- `$security-best-practices` when the job needs secure-by-default implementation or code-review guidance.
- `$security-threat-model` when trust boundaries, attacker capabilities, or abuse-path mapping materially affect the work.
- `$security-ownership-map` when sensitive ownership gaps or disclosure routing matter.

## Hard Boundaries

- Defensive use only. Do not weaponize findings or provide offensive exploit steps.
- Stay inside authorized local context and the user-approved scope.
- Use the minimum safe proof needed. Prefer read-only inspection, targeted tests, narrow local reproductions, and redacted evidence.
- If a real third-party vulnerability is confirmed, shift to maintainer-first remediation and coordinated disclosure. Do not publish harmful detail by default.

## Workflow

### 1. Scope and authority

- Confirm the exact repo, path, service, or config surface being touched and whether it is first-party or third-party.
- Separate confirmed scope from inferred adjacent risk.

### 2. Build the attack-surface map

- Focus on entry points, trust boundaries, secrets, auth/session state, persistence, network listeners, file uploads/parsers, dependency/update surfaces, model prompts/tool calls, and outbound data sinks.
- Load only the references you actually need.

### 3. Hunt for defender-relevant issues

- Look for bugs, crashes, unsafe defaults, privilege drift, injection paths, prompt/data leakage, secret exposure, broken authorization, insecure temp files, arbitrary file access, deserialization or parser risk, dependency/script execution risk, SSRF/RCE-style classes, and logging or telemetry leaks.
- For model/tool systems, check prompt injection resistance, tool-boundary enforcement, output screening, and least-secret context.
- If a tool-assisted sweep would materially improve confidence, use the safe shortlist in `references/tooling-and-sources.md` and keep third-party sources in discovery-only posture until they have been rewritten or admitted locally.

### 4. Verify safely

- Use the least destructive confirmation possible.
- Prefer existing tests, targeted new tests, mock data, local-only repros, static inspection, and bounded smokes over broad exploit trials.
- Stop and escalate if confirmation would risk user data, uptime, or cross an authorization boundary.

### 4a. Use the repo's CI as a validation map

- Do not treat every third-party lane as `run everything`.
- Capture the current head SHA and classify the CI state before acting:
  - `current red`: the failing check is attached to the current head
  - `stale red`: the badge or notification points at an older head or a later rerun on the current head passed
  - `pending`: the lane is still deciding and should not be overfit yet
- Derive the narrowest local proof from the target repo's own workflow and script structure.
- Prefer repo-native change routing when it exists:
  - changed-scope or docs-only detectors
  - changed-extension or changed-package matrices
  - dedicated protocol, contracts, gateway, or workflow-hardening lanes
- Keep the rerun aligned to the ownership surface:
  - workflow or supply-chain changes: actionlint, secret scan, workflow audit, explicit permissions checks
  - type/lint failures: the repo's main `check` or equivalent gate
  - build smoke failures: the repo's narrow build/smoke lane, not its full test matrix
  - protocol/contracts failures: only the protocol/contracts commands
  - extension-specific failures: rerun only the changed extension lane and any paired core tests
  - gateway/watch harness failures: rerun only the harness if the touched surface actually owns it
- OpenClaw is a good reference pattern here:
  - `check` maps to `pnpm check` plus `pnpm build:strict-smoke`
  - `checks-fast-contracts-protocol` maps to `pnpm test:contracts` plus `pnpm protocol:check`
  - `checks-node-extensions-shard-*` should drive extension-targeted validation, not a blind whole-repo retest
  - `gateway-watch-regression` is a dedicated harness lane and should stay isolated
- If the red is stale, do not churn code just to satisfy an outdated badge. Harvest the lane structure anyway and keep it as the validation map for the next live head.

### 5. Remediate and document

- Fix or reduce risk with durable changes, not cosmetic notes.
- Clearly distinguish confirmed findings, likely risks, and unverified concerns.
- For third-party lanes, prepare a maintainer-friendly summary with impact, affected surface, safe repro notes, and mitigation or a candidate patch.
- Record the current head SHA, the validation lanes used, and whether any red CI was stale or live.

### 6. Final pass

- Re-check the touched surface after changes.
- Call out residual risk, missing tests, disclosure obligations, and whether the contribution is safe to submit.

## Priority Order

- Active secret leakage or cross-boundary data exposure
- Auth, session, or permission failures
- Remote or local code execution paths
- Unsafe parsing, file access, or dependency execution
- Prompt injection, tool misuse, or model-context leaks
- Integrity or availability failures that could become abuse paths
- Lower-severity hardening gaps

## Reporting Contract

- Lead with findings, ordered by severity.
- For each finding, state confirmed vs inferred status, impacted surface, minimal evidence, and the safest mitigation.
- If there are no findings, say so explicitly and mention residual risk or testing gaps.

## References

- Anthropic-inspired defensive patterns and disclosure posture: `references/defender-patterns.md`
- Safe external tooling and source shortlist: `references/tooling-and-sources.md`
