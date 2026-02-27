# VS Code Skill Handling and Overlay Recovery

This document records how VS Code/Codex skill handling interacts with this repository's overlay skills.

## Non-Conflict Policy

- VS Code/Codex built-in skills are upstream and are not modified by this repository.
- This repository only adds and moderates an overlay skill set from `skill-candidates/`.
- Built-ins remain enabled; overlay skills are restored and validated on top.

## Incident Record

Observed on: **February 27, 2026**

Observed state:

- The Codex UI skill list showed built-ins only.
- Repository overlay skills were not present in the active installed list.
- Installed built-ins had older synchronized timestamps, indicating a host-level skill refresh/reset event.

Most likely cause:

- A VS Code/Codex built-in skill refresh reset the active local skill inventory to baseline built-ins, leaving repository overlay skills unapplied.

## Recovery Procedure (Executed)

1. Verify overlay coverage:

```powershell
$repoSkills = Get-ChildItem -Directory skill-candidates | Select-Object -ExpandProperty Name
$installed = Get-ChildItem -Directory "$env:USERPROFILE\.codex\skills" | Select-Object -ExpandProperty Name
$missing = $repoSkills | Where-Object { $_ -notin $installed }
$missing
```

2. Restore overlay skill directories additively:

```powershell
$srcRoot = Resolve-Path "skill-candidates"
$dstRoot = Join-Path $env:USERPROFILE ".codex\skills"
Get-ChildItem -Directory $srcRoot | ForEach-Object {
  $dst = Join-Path $dstRoot $_.Name
  if (!(Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
  Copy-Item -Recurse -Force (Join-Path $_.FullName '*') $dst
}
```

3. Re-check coverage:

```powershell
$repoSkills = Get-ChildItem -Directory skill-candidates | Select-Object -ExpandProperty Name
$installed = Get-ChildItem -Directory "$env:USERPROFILE\.codex\skills" | Select-Object -ExpandProperty Name
($repoSkills | Where-Object { $_ -notin $installed }).Count
```

Expected result: `0`.

4. Validate churn safety after restore:

```bash
python3 scripts/arbitrate_skills.py <skills...> \
  --source-dir skill-candidates \
  --personal-lockdown \
  --json-out /tmp/restore-arbiter.json
```

## Ongoing Protection Plan

1. Keep `skill-candidates/` as source-of-truth for overlay skills.
2. After VS Code/Codex updates, run overlay coverage check and restore if needed.
3. Run `skill-arbiter` safety admission for changed/new skills before enabling broad use.
4. Keep `references/skill-catalog.md` updated whenever skills change.
5. Keep policy docs in lockstep:
   - `AGENTS.md`
   - `README.md`
   - `CONTRIBUTING.md`
   - `SKILL.md`
   - `.github/pull_request_template.md`

## Audit Addendum

The full installed-skill churn audit should include:

- top-level built-ins under `$env:USERPROFILE\.codex\skills`
- system built-ins under `$env:USERPROFILE\.codex\skills\.system`
- repository overlay candidates from `skill-candidates/`

This ensures regressions are caught across both upstream and overlay layers.
