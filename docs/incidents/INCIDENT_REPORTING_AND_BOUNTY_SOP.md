# Incident Reporting and Bounty Triage SOP

## Purpose

Agent failures must not remain buried in chat transcripts, backend logs, screenshots, workstream receipts, or repeated retries. When Codex, ChatGPT, a local model, an MCP server, LM Studio, OpenClaw, STARFRAME, or another connected tool exposes a reproducible defect, the work must stop at the appropriate circuit breaker, preserve evidence, and route the defect to the correct owner while the state is still recoverable.

This SOP is not permission to flood issue trackers or mislabel ordinary defects as security vulnerabilities. It requires evidence quality, duplicate search, claim boundaries, correct public/private handling, and one canonical receiving route per defect.

## Trigger conditions

Start incident handling when any of the following occurs:

- the same deterministic tool failure repeats twice;
- automatic compaction completes without meaningful working headroom;
- completed-versus-pending state degrades across compaction;
- the agent repeats a plan or previously completed work without advancing;
- requested tools, model, authority, or output surface silently differ from the effective run;
- backend/configuration state is described as foreground success before live acceptance;
- a health endpoint reports ready while the required execution path is unavailable;
- a relevant public service incident overlaps a failing or usage-heavy run;
- process, memory, log, or evidence growth crosses the configured budget;
- active-turn/session state becomes ambiguous;
- a possible credential, authorization, privacy, account-integrity, or third-party security boundary is involved.

## Immediate circuit breaker

1. Stop the failing autonomous lane before a third identical deterministic retry.
2. Do not restart, clean, rotate, or mutate the affected state until required evidence is preserved.
3. Record the last known good state, first bad state, and exact requested-versus-effective capability.
4. Produce a bounded handoff. Do not carry the complete chat or raw tool history into another model context.
5. Notify the operator that production work has paused for incident routing.

## Evidence packet

Create one `incident_consult_packet` containing:

- incident ID and timestamps;
- product, version, operating system, model, reasoning mode, and affected surface;
- exact minimal reproduction;
- expected and observed behavior;
- requested versus effective model, tools, authority, and acceptance surface;
- sanitized error and tool excerpts;
- reproduction count and retry chronology;
- measurable user impact, including usage, elapsed time, storage, memory, and lost progress where supported;
- last known good state and rollback point;
- evidence file hashes and private evidence locations;
- public-safe screenshots or excerpts;
- candidate local and upstream owners;
- security-boundary questions;
- missing telemetry and uncertainty.

Never infer token counts from percentage screenshots. Never publish credentials, cookies, account identifiers, private repository content, private endpoints, or actionable exploit details.

## Codex to ChatGPT reporting consult

When the circuit breaker activates, Codex must hand the bounded packet to a ChatGPT/reporting consult rather than continuing to code in silence.

The consult must:

1. search local and upstream trackers for duplicates;
2. distinguish a corroborating comment from a materially new defect;
3. classify the proper owner and disclosure channel;
4. preserve factual claim boundaries and avoid unsupported intent attribution;
5. prepare a redacted public report when safe;
6. keep security-sensitive evidence private;
7. return a machine-readable disposition and next action;
8. report the result in the active operator surface before production resumes.

Allowed dispositions:

- `local_repair`
- `upstream_existing_issue_corroboration`
- `upstream_new_product_issue`
- `support_usage_or_billing_review`
- `private_security_incident`
- `security_bug_bounty_candidate`
- `safety_bug_bounty_candidate`
- `duplicate`
- `insufficient_evidence`
- `out_of_scope`

## Duplicate and canonicalization rules

- Search before filing.
- Corroborate an existing issue when the same invariant and remediation owner apply.
- Create a new issue only when the symptom, boundary, telemetry requirement, or remediation owner is materially distinct.
- Move unique evidence into the canonical issue before closing a duplicate.
- Keep one open parent ledger for each incident cluster.
- Filing is not resolution. Track owner, response, patch, release, regression, and operator-visible acceptance.

## Public product issue route

Use a public product issue for reliability, performance, context management, quota communication, renderer/session behavior, false progress, lifecycle leaks, or usability defects when no security boundary has been demonstrated.

A good report contains:

- narrow title;
- environment and version;
- reproducible steps;
- observed and expected behavior;
- measurable impact;
- safe diagnostics;
- related issues and the exact distinction;
- requested telemetry or circuit breaker;
- redacted evidence.

## Support and usage-review route

A public issue cannot restore usage or decide account remediation. Build a separate private session-level packet containing account/session identifiers, authoritative analytics evidence, incident overlap, compaction/retry chronology, useful progress, and uncertainty. Submit it through the appropriate support or usage-review channel and retain the reference and disposition.

## Security and Safety Bug Bounty screen

Every incident receives a bounty eligibility screen, but ordinary defects must not be called vulnerabilities without a demonstrated boundary and impact.

Potential Security Bug Bounty indicators include:

- unauthorized access or action;
- permission or approval bypass;
- cross-account or cross-tenant data exposure;
- secret or credential disclosure;
- account/platform integrity compromise;
- sandbox or isolation escape;
- attacker-controlled resource exhaustion with material impact;
- execution beyond the user's authorized scope.

Potential Safety Bug Bounty indicators include reproducible AI-specific abuse or agentic risk that creates tangible harm, such as reliable third-party prompt injection causing sensitive-data exfiltration or harmful agent actions.

Reliability, quota visibility, compaction, generic performance, poor answers, renderer failures, and ordinary local configuration defects remain product issues unless a concrete security, privacy, integrity, authorization, or material-harm boundary is established.

Research must be limited to owned or explicitly authorized systems and comply with third-party terms. Preserve exploit details privately and use coordinated disclosure before public technical release.

Official policy references:

- OpenAI coordinated vulnerability disclosure policy: https://openai.com/policies/coordinated-vulnerability-disclosure-policy/
- OpenAI Security Bug Bounty overview: https://openai.com/index/bug-bounty-program/
- OpenAI Safety Bug Bounty overview: https://openai.com/index/safety-bug-bounty/

## Closure criteria

An incident closes only when all applicable items exist:

1. reproducible evidence;
2. canonical owner/receiving channel;
3. local patch, upstream disposition, support outcome, or bounty disposition;
4. focused regression;
5. merged or released state where applicable;
6. operator-visible acceptance;
7. evidence retention and safe cleanup decision;
8. completion status updated from operational evidence rather than activity volume.

A plan, receipt, screenshot, toggle, large diff, passing unrelated test, issue filing, or backend-only result is not closure.
