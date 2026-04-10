# Defender Patterns

Use these patterns to keep the `white-hat` lane defensive, practical, and maintainer-safe.

## Core posture

- Defender first, never offensive.
- Human-validate important findings before treating them as real.
- Use the minimum safe proof needed to confirm a weakness.
- Prefer remediation, guardrails, and disclosure discipline over exploit detail.

## Anthropic-inspired takeaways

These are defensive patterns derived from Anthropic's public guidance around Mythos, guardrails, prompt leakage, and coordinated vulnerability disclosure.

### 1. Minimize secret exposure

- Do not put secrets, private prompts, or proprietary context into the model unless the task truly needs it.
- Prefer least-secret context and explicit isolation over clever prompt tricks.

### 2. Resist prompt and tool boundary failures

- Treat prompt injection as a real input-validation problem.
- Keep tool permissions narrow and make trust boundaries explicit.
- Re-check whether untrusted text can alter hidden instructions, tool calls, or downstream actions.

### 3. Monitor outputs for leaks

- Review model outputs, logs, traces, and generated artifacts for prompt leakage, secret exposure, and unsafe action suggestions.
- Prefer output screening and post-processing before layering on brittle prompt complexity.

### 4. Balance guardrails with functionality

- Leak prevention that makes the system too complex can reduce quality elsewhere.
- Favor simpler isolation, clearer structure, and periodic audits before stacking fragile prompt defenses.

### 5. Coordinate disclosure like a maintainer ally

- If a real vulnerability is found in third-party software, prepare a maintainer-friendly report with impact, affected surface, safe repro notes, and a mitigation or candidate patch when possible.
- Avoid public harmful detail before a fix is available unless there is a clear defender need and explicit authorization.
- Pace reports so maintainers can absorb them and prioritize active exploitation separately.

## Practical checklist

- What secrets or sensitive context are in scope?
- What are the real entry points and trust boundaries?
- Can untrusted input change auth, permissions, tool use, or hidden instructions?
- Can output leak prompts, tokens, credentials, or private data?
- Can logs, temp files, caches, or telemetry expose sensitive material?
- Is there a safe, narrow way to confirm the issue?
- What is the least disruptive durable fix?
- If this is third-party software, what disclosure and maintainer support does the situation require?
