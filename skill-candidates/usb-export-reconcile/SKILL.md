---
name: "usb-export-reconcile"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Review and reconcile USB-delivered repo exports as Git-like sources. Use when a USB drive carries a repo clone or host bundle that must be compared, reviewed, backed up, and only then applied."
---

# USB Export Reconcile

Use this skill when removable-media exports must be handled with the same discipline as GitHub.

## Workflow

1. Treat the USB export as a source-of-truth candidate, not an automatic overwrite source.
2. Run a review-only compare first and capture a machine-readable diff report.
3. Separate:
   - matching files
   - changed files
   - USB-only files
   - local-only files
4. Do not assume the USB wins blindly.
5. Preserve a local backup/snapshot before any reconcile step.
6. Reconcile intentionally only after review is complete.
7. Validate the canonical startup path after reconcile.
8. Report remaining drift explicitly instead of claiming the repo is fully integrated.

## Required Rules

- No destructive mirror delete unless explicitly approved.
- No “fully reconciled” or “fully integrated” claim before diff review plus post-reconcile validation.
- If the USB export is not final yet, stay in review-only mode.

## Scope Boundary

Use this skill only for USB/removable-media reconcile lanes.

Do not use it for:

1. Normal GitHub remote workflows.
2. Arbitrary file-copy operations without a repo or bundle review context.
3. Desktop startup debugging by itself.

## Loopback

If this lane is unresolved, blocked, or ambiguous:

1. Capture the USB path, local path, and review-report location.
2. Route back through `$skill-hub` for chain recalculation.
3. Resume only after the updated chain returns a deterministic next step.
