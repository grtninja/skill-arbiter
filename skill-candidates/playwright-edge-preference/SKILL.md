---
name: playwright-edge-preference
description: Run Playwright browser automation with Microsoft Edge as the default channel. Use when users request Edge-specific validation, screenshots, or parity checks while keeping deterministic low-churn automation flow.
---

# Playwright Edge Preference

Use this skill when browser tasks must run in Microsoft Edge.

## Workflow

1. Confirm Microsoft Edge is installed on the host.
2. Run Playwright automation with `channel="msedge"` as default.
3. Keep runs deterministic (bounded scripts, explicit output paths).
4. Fail closed if Edge is unavailable; do not silently switch browsers.

## Scope Boundary

Use this skill for Edge-channel browser execution and parity checks.

Do not use this skill for:

1. Non-browser repo operations.
2. General skill routing decisions.
3. Asset-heavy browser workflows that bypass no-churn controls.

## Edge Availability Check (PowerShell)

```powershell
$edgeCandidates = @(
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$edgePath = $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edgePath) { throw "Microsoft Edge not found on this host." }
$edgePath
```

## Edge Run Patterns

Node one-shot (headless screenshot):

```bash
node -e "const { chromium } = require('playwright'); (async () => { const browser = await chromium.launch({ channel: 'msedge', headless: true }); const page = await browser.newPage(); await page.goto('https://example.com', { waitUntil: 'domcontentloaded' }); await page.screenshot({ path: 'edge-shot.png', fullPage: true }); await browser.close(); })();"
```

Playwright test project pattern:

```bash
npx playwright test --project=edge
```

## Integration Notes

- Pair with `playwright-safe` when churn sensitivity is high.
- Use `skill-hub` first if lane selection is still ambiguous.

## References

- `references/edge-commands.md`

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture current evidence and failure context.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
