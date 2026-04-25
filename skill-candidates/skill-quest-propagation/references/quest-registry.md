# Quest Registry

Use the generated quest registry as the durable inventory of prior and active quest state.

## Source Coverage

- `<PRIVATE_REPO_ROOT>\reports\**\next_quest.md`
- `%USERPROFILE%\.codex\workstreams\*quest*.json`

## Included Entry Types

- workstream state files with `task` plus `lanes`
- quest reports with a top-level `quest` object
- resume contracts with a top-level `resume_contract`
- non-empty `next_quest.md` handoff notes

## Generated Outputs

- `references/quest-registry.generated.json`
- `references/quest-registry.generated.md`

## Minimum Use Pattern

1. Rebuild the registry before starting a new governed quest after interruption.
2. Update the active workstream state file.
3. Update the active `next_quest.md` handoff note.
4. Rebuild the registry again so the latest quest is represented in the same place as the older ones.

## Quality Checks

- the active quest appears in the latest registry run
- the current quest note path is represented or intentionally blank
- the latest quest next action matches the live workstream state
- older quest files are harvested instead of forgotten in local workstreams
