---
name: skill-dependency-fan-out-inspector
description: Inspect skill-to-skill dependencies and detect fan-out, cycles, and N+1 invocation risk. Use when scaling skill stacks or diagnosing hidden cross-skill cost/latency amplification.
---

# Skill Dependency Fan-Out Inspector

Use this skill to make cross-skill invocation risk explicit before it causes cost or latency blowups.

## Workflow

1. Scan skill metadata under `skill-candidates/`.
2. Build a dependency graph from explicit `$skill-name` references.
3. Flag fan-out hotspots, high transitive reach, and cycles.
4. Emit JSON and optional DOT graph artifacts.

## Inspect Graph

```bash
python3 "$CODEX_HOME/skills/skill-dependency-fan-out-inspector/scripts/dependency_inspector.py" \
  --skills-root skill-candidates \
  --fanout-threshold 4 \
  --transitive-threshold 12 \
  --json-out /tmp/skill-dependency-report.json \
  --dot-out /tmp/skill-dependency-graph.dot \
  --format table
```

Use `--include-plain-names` when legacy skills mention dependencies without `$` prefixes.

## References

- `references/inspection-workflow.md`
- `references/graph-contract.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
