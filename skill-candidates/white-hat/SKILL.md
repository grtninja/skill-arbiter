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

### 5. Remediate and document

- Fix or reduce risk with durable changes, not cosmetic notes.
- Clearly distinguish confirmed findings, likely risks, and unverified concerns.
- For third-party lanes, prepare a maintainer-friendly summary with impact, affected surface, safe repro notes, and mitigation or a candidate patch.

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
