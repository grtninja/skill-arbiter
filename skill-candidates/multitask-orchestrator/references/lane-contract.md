# Lane Contract

Use this contract for each multitask lane.

## Required Fields

```json
{
  "lane_id": "lane-a",
  "objective": "one sentence scope",
  "inputs": ["path/or/context"],
  "skills": ["skill-hub", "specific-skill"],
  "checks": ["command --or gate"],
  "artifacts": ["path/to/report.json"],
  "status": "pass|fail|blocked",
  "next_action": "deterministic next step"
}
```

## Merge Checklist

1. Every lane has complete required fields.
2. Every `pass` lane has at least one verification artifact.
3. Every `fail` lane includes root cause evidence.
4. Every `blocked` lane includes a loopback resume action.
5. Final merged output references all lane artifacts.

