# Repo D Sandbox Guardrails

- Windows-first development and packaging.
- No GitHub Actions or CI workflows in this repo.
- Keep visuals deterministic unless a toggle/preset explicitly changes behavior.
- Keep assets local; no surprise runtime downloads.
- Keep npm workspace flow valid: `npm install`, `npm run dist`, `npm run dev`.
- Keep `docs/SCOPE_TRACKER.md` and `docs/TODO.md` current for scoped changes.
