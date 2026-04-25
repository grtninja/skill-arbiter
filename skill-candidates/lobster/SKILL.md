---
name: "lobster"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Execute multi-step workflows with approval checkpoints via the Lobster pipeline engine. Use when the user wants repeatable automations (email triage, PR monitoring, scheduled syncs), when actions need human approval before executing (send, post, delete), or when multiple tool calls should run as one deterministic pipeline operation."
---

# Lobster

Execute multi-step workflows with approval checkpoints. Lobster pipelines are deterministic (no LLM variance), resumable via tokens, and return structured JSON output.

## When to Use Lobster

| User intent | Use Lobster? |
| ----------- | ------------ |
| "Triage my email" | Yes — multi-step, may send replies |
| "Send a message" | No — single action, use tool directly |
| "Check my email every morning and ask before replying" | Yes — scheduled workflow with approval |
| "What's the weather?" | No — simple query |
| "Monitor this PR and notify me of changes" | Yes — stateful, recurring |

**Do not use** for simple single-action requests, queries needing LLM interpretation mid-flow, or one-off non-repeatable tasks.

## Workflow

1. Identify whether the user request involves multi-step automation, approval gates, or recurring operations — if yes, use Lobster.
2. Run the pipeline:
   ```json
   { "action": "run", "pipeline": "gog.gmail.search --query 'newer_than:1d' --max 20 | email.triage" }
   ```
3. Check the response `status` field:
   - `"ok"` — pipeline completed; present `output` to the user.
   - `"needs_approval"` — present the `requiresApproval.prompt` and items to the user.
4. If approval needed, collect user confirmation and resume:
   ```json
   { "action": "resume", "token": "<resumeToken>", "approve": true }
   ```
5. Present final output to the user.

## Key Behaviors

- **Deterministic**: Same input produces same output (no LLM variance in pipeline execution).
- **Approval gates**: `approve` command halts execution, returns a `resumeToken`.
- **Resumable**: Use `resume` action with the token to continue after approval.
- **Structured output**: Always returns JSON envelope with `protocolVersion`, `status`, `output`, and `requiresApproval`.

## Example Pipelines

```bash
# Email triage — classify into needs_reply, needs_action, fyi
gog.gmail.search --query 'newer_than:1d' --max 20 | email.triage

# Email triage with approval gate
gog.gmail.search --query 'newer_than:1d' | email.triage | approve --prompt 'Process these?'
```

## Guardrails

- Use local or trusted tools only; avoid untrusted install pipelines.
- Do not paste secrets/tokens into chat output.
- Keep outputs in deterministic local paths for reproducible review.
