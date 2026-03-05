# OpenClaw NullClaw Integration Map

Use this map to convert upstream third-party changes into local integration lanes.

## Source-to-lane mapping

1. OpenClaw ACP/router and agent orchestration changes:
   - Route to Repo A coordinator routing and cross-agent dispatch checks.
   - Route to skill-catalog/chain updates for agent-skill coverage.
2. NullClaw provider/router/channel changes:
   - Route to MX3 model-router and policy derivation checks.
   - Route to AvatarCore provider-profile routing checks when request metadata or env profile behavior is affected.
3. Gateway/network posture changes:
   - Route to router-profile docs and environment variable mapping across repos.

## Minimum reconciliation artifacts

- Third-party intake JSON (`skills-third-party-intake`)
- Third-party attribution markdown update
- Skill auditor JSON for changed/new skills
- Arbiter admission JSON for changed/new skills
- Passing test evidence from each impacted repository
