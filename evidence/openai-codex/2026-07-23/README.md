# Codex Desktop repeated-compaction evidence — 2026-07-23

This directory preserves a public-safe visual exhibit for [openai/codex#35032](https://github.com/openai/codex/issues/35032).

## Exhibit

![Repeated automatic compaction between tool operations](./repeated-compaction-loop-redacted.svg)

The crop shows a production Codex Desktop thread repeatedly alternating among:

- `Context automatically compacted`
- `Run a command` / `Run commands`
- another automatic compaction event

The broader captured session visibly returned from compaction with the context meter near 80% full, leaving only limited working headroom before the next cycle. The canonical issue contains the reproduction, expected behavior, impact, and requested telemetry.

## Redaction and provenance

- Observed: July 23, 2026
- Product: Codex Desktop
- Platform: Windows 11 Pro
- Evidence class: operator screenshot, cropped and redacted
- Preserved text: only the repeated tool-operation and automatic-compaction event labels
- Removed: private task text, repository names and paths, integration names, account details, session identifiers, and usage/account metadata
- Embedded raster SHA-256: `9FEB16A84683A59EEB62E3BEDD958F1DF71ADF21FF70CE091DD961BB32A358C4`

The SVG embeds the redacted raster so the exhibit is self-contained and cannot silently depend on an external image host.

## Evidentiary boundary

This exhibit supports the claim that repeated automatic compaction events occurred between a small number of visible tool operations. By itself, it does **not** prove the root cause, server-side token accounting, or whether every retained context token was necessary. Those require product telemetry.

## Canonical tracker map

- [#35032](https://github.com/openai/codex/issues/35032) — successful compaction leaves the thread about 80% full
- [#34322](https://github.com/openai/codex/issues/34322) — compact/resume/re-read loop
- [#34095](https://github.com/openai/codex/issues/34095) — execution-frontier degradation across repeated compactions
- [#34971](https://github.com/openai/codex/issues/34971) — cached-context reprocessing, latency, state growth, and excessive usage

## Requested product invariant

A compaction event must either:

1. reclaim substantial working headroom and preserve a bounded execution frontier; or
2. fail visibly, stop further autonomous retries, and emit a bounded handoff/checkpoint.

A success event that immediately resumes near the next compaction threshold is not operational success.
