# Third-Party Intake Rubric

The intake script emits three scores per discovered skill:

- `compatibility`: packaging/readiness for this repo's skill format.
- `quality`: clarity and maintainability of instructions and structure.
- `security`: risk posture from deterministic static checks.

Recommendation thresholds:

1. `admit`
   - no blocker findings
   - `security >= 0.75`
   - `quality >= 0.55`
2. `manual_review`
   - no blocker findings
   - `security >= 0.55`
3. `reject`
   - any blocker finding, or low security score

Blocker examples:

- high-risk command snippets (`curl | sh`, `Invoke-Expression`, destructive shell payloads)
- unsafe markdown links (absolute paths, parent traversal, script targets, unsupported schemes)

Warning examples:

- script suffix files in third-party skill packs
- missing frontmatter fields
- missing `agents/openai.yaml`
- sensitive marker terms (`token`, `secret`, `api_key`, etc.)
