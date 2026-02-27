# Edge Command Reference

## Verify Edge Installation

```powershell
$edgeCandidates = @(
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$edgeCandidates | Where-Object { Test-Path $_ }
```

## Node + Playwright (Edge Channel)

```bash
node -e "const { chromium } = require('playwright'); (async () => { const browser = await chromium.launch({ channel: 'msedge', headless: true }); const page = await browser.newPage(); await page.goto('https://example.com', { waitUntil: 'domcontentloaded' }); await page.screenshot({ path: 'edge-shot.png', fullPage: true }); await browser.close(); })();"
```

## Playwright Test Project Example

`playwright.config.ts` fragment:

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    {
      name: 'edge',
      use: {
        ...devices['Desktop Edge'],
        channel: 'msedge',
      },
    },
  ],
});
```

Run:

```bash
npx playwright test --project=edge
```

## Failure Policy

If Edge is missing, fail closed and return installation guidance. Do not auto-switch to another browser unless explicitly approved.
