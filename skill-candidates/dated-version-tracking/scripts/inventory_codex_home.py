#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any


CODEX_NATIVE_REQUIRED = {
    "auth.json": "Codex authentication state. Never copy into public output.",
    "config.toml": "Live Codex config.",
    "sessions": "Codex conversation/session state.",
    "logs": "Codex logs directory.",
    ".sandbox": "Current Codex sandbox state.",
    ".codex-global-state.json": "Codex app/global state.",
    "state_5.sqlite": "Codex state database.",
    "logs_2.sqlite": "Codex log database.",
}
ACTIVE_RUNTIME_PATTERNS = (
    "state_*.sqlite",
    "state_*.sqlite-wal",
    "state_*.sqlite-shm",
    "logs_*.sqlite",
    "logs_*.sqlite-wal",
    "logs_*.sqlite-shm",
)
STARFRAME_ADDED = {
    "memories": "Local continuity and governance memory surfaces.",
    "skills": "Local first-party skills and plugin skills.",
    "workstreams": "STARFRAME/Codex workstream ledgers and evidence.",
    "config.stale": "Config cleanup, stale evidence, and inventory lane.",
    "codex-plugins": "Local plugin material if present.",
    "plugins": "Local plugin material if present.",
}
BROKEN_PATTERNS = (
    "*.broken",
    "*.fail",
    "*.fail[0-9]*",
    ".sandbox.broken",
    "logs_*.sqlite.broken",
)
STALE_PATTERNS = (
    "config.toml.bak*",
    "config.toml.pre-*.bak",
    "config.toml.bak-before-*",
)
PRIVATE_PATTERNS = (
    "auth.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def classify(path: Path) -> dict[str, Any]:
    name = path.name
    stat = path.stat()
    category = "unknown-review-required"
    action = "review-before-touch"
    reason = "No rule matched."

    if name in CODEX_NATIVE_REQUIRED:
        category = "codex-native-required"
        action = "keep"
        reason = CODEX_NATIVE_REQUIRED[name]
    if _matches(name, ACTIVE_RUNTIME_PATTERNS):
        category = "active-runtime-do-not-touch"
        action = "keep"
        reason = "Active runtime database or WAL/SHM sidecar."
    if name in STARFRAME_ADDED:
        category = "starframe-added"
        action = "keep"
        reason = STARFRAME_ADDED[name]
    if _matches(name, STALE_PATTERNS):
        category = "stale-evidence"
        action = "move-to-config.stale"
        reason = "Historical config backup; not live source of truth."
    if _matches(name, BROKEN_PATTERNS):
        category = "broken-evidence"
        action = "move-to-config.stale"
        reason = "Explicitly marked broken or failed artifact."
    if _matches(name, PRIVATE_PATTERNS):
        category = "codex-native-required"
        action = "keep-private"
        reason = "Authentication/private state. Never expose."

    return {
        "name": name,
        "path": str(path),
        "kind": "directory" if path.is_dir() else "file",
        "category": category,
        "recommended_action": action,
        "reason": reason,
        "last_write_time_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "length": stat.st_size if path.is_file() else None,
        "sha256": _sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory .codex root ownership and cleanup status.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--output")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    codex_home = Path(args.codex_home).expanduser()
    output = Path(args.output).expanduser() if args.output else codex_home / "config.stale" / "codex-home-inventory.json"
    items = [classify(path) for path in sorted(codex_home.iterdir(), key=lambda p: p.name.lower())]
    summary: dict[str, int] = {}
    for item in items:
        summary[item["category"]] = summary.get(item["category"], 0) + 1
    manifest = {
        "schema_version": 1,
        "generated_at": _now(),
        "codex_home": str(codex_home),
        "output": str(output),
        "privacy_note": "Inventory records filenames, sizes, timestamps, hashes, and categories only; it does not read auth contents.",
        "summary": summary,
        "items": items,
    }
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"wrote {output}")
        print(json.dumps({"summary": summary}, indent=2, sort_keys=True))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
