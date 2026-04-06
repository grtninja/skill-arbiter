# Open Diff Finding Taxonomy

Use this reference to classify recent multi-repo open-diff findings.

## Primary Categories

### release_hygiene_missing

Use when release-impacting files changed without the required version/changelog updates.

Route to:

- `$skill-arbiter-release-ops`

### docs_lockstep_missing

Use when behavior-impacting files changed without matching README, scope, runbook, or reconciliation-doc updates.

Route to:

- `$docs-alignment-lock`

### tests_missing

Use when code changed without corresponding test coverage or targeted verification updates.

Route to:

- `$skill-common-sense-engineering`

### startup_acceptance_drift

Use when desktop launchers, window lifecycle, helper processes, or shortcut ownership changed.

Route to:

- `$desktop-startup-acceptance`

### policy_contract_drift

Use when shared contracts, boundary docs, endpoint authority, or cross-repo assumptions drift together.

Route to:

- `$skill-enforcer`

## Output Table

For each repo, produce:

- `repo`
- `gap_category`
- `severity`
- `evidence`
- `suggested_skill`
- `next_action`
