# Graph Contract

## Report Keys

- `generated_at`
- `skills_root`
- `graph`
- `metrics`
- `nodes[]`
- `edges[]`
- `out_degree[]`
- `in_degree[]`
- `fanout_hotspots[]`
- `n_plus_one_risks[]`
- `cycles[]`
- `recommendations[]`

## Edge Shape

- `from`
- `to`
- `type` (`explicit_dollar` | `plain_name`)

## Risk Heuristics

- Fan-out hotspot: `out_degree >= fanout_threshold`
- N+1 risk: `transitive_reach >= transitive_threshold`
- Cycle risk: any directed cycle length >= 2 edges

## DOT Export

When `--dot-out` is provided, a Graphviz DOT file is generated:

- one node per skill
- one directed edge per dependency
- edge label indicates detection type
