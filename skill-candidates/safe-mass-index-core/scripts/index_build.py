#!/usr/bin/env python3
"""Build a deterministic, metadata-only repository index without rg usage."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_EXCLUDES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".cache",
    ".codex-index",
}

TEXT_EXTS = {
    ".c",
    ".cc",
    ".cfg",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsonl",
    ".kt",
    ".m",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

BINARY_EXTS = {
    ".7z",
    ".a",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dylib",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".lib",
    ".mp3",
    ".mp4",
    ".o",
    ".obj",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".svgz",
    ".tar",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}

LANG_BY_EXT = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".kt": "kotlin",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".txt": "text",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass
class RunCounters:
    """Accumulates index build counters for manifest and run report."""

    files_seen: int = 0
    files_indexed: int = 0
    files_reused: int = 0
    files_updated: int = 0
    files_removed: int = 0
    files_unreadable: int = 0
    dirs_skipped: int = 0
    symlinks_skipped: int = 0
    bytes_read: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "files_seen": self.files_seen,
            "files_indexed": self.files_indexed,
            "files_reused": self.files_reused,
            "files_updated": self.files_updated,
            "files_removed": self.files_removed,
            "files_unreadable": self.files_unreadable,
            "dirs_skipped": self.dirs_skipped,
            "symlinks_skipped": self.symlinks_skipped,
            "bytes_read": self.bytes_read,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build metadata-only index with bounded incremental mode")
    parser.add_argument("--repo-root", default=".", help="Repository root to index")
    parser.add_argument("--index-dir", default=".codex-index", help="Index directory path")
    parser.add_argument(
        "--mode",
        choices=("incremental", "full"),
        default="incremental",
        help="Build mode",
    )
    parser.add_argument("--max-files-per-run", type=int, default=12000, help="Max files to process")
    parser.add_argument("--max-seconds", type=int, default=25, help="Max wall-clock seconds")
    parser.add_argument(
        "--max-read-bytes",
        type=int,
        default=64 * 1024 * 1024,
        help="Max bytes read for lightweight text probing",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude (repeatable)",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional extra run report path; run.json is always written under index-dir",
    )
    parser.add_argument(
        "--sharded",
        action="store_true",
        help="Store records under shards/<top-level>.jsonl instead of files.jsonl",
    )
    return parser.parse_args()


def normalize_index_dir(repo_root: Path, index_dir: str) -> Path:
    candidate = Path(index_dir).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def normalize_excludes(index_dir: Path, excludes: list[str]) -> set[str]:
    values = {name.strip() for name in DEFAULT_EXCLUDES}
    values.update({item.strip() for item in excludes if item.strip()})
    values.add(index_dir.name)
    return values


def load_state(path: Path) -> tuple[dict[str, Any], bool, str]:
    """Load previous state entries. Returns entries, fallback flag, and reason."""

    if not path.is_file():
        return {}, False, ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, True, "corrupt_state"

    if not isinstance(payload, dict):
        return {}, True, "invalid_state_shape"
    if payload.get("schema_version") != SCHEMA_VERSION:
        return {}, True, "state_schema_mismatch"
    entries = payload.get("entries", {})
    if not isinstance(entries, dict):
        return {}, True, "invalid_state_entries"

    sanitized: dict[str, Any] = {}
    for key, value in entries.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        fingerprint = value.get("fingerprint")
        record = value.get("record")
        if not (isinstance(fingerprint, list) and len(fingerprint) == 4 and isinstance(record, dict)):
            continue
        sanitized[key] = {"fingerprint": fingerprint, "record": record}
    return sanitized, False, ""


def guess_language(ext: str) -> str:
    if ext in LANG_BY_EXT:
        return LANG_BY_EXT[ext]
    return "unknown"


def is_probably_text(path: Path, counters: RunCounters, max_read_bytes: int) -> tuple[bool, bool]:
    """Probe a small prefix when extension is unknown. Returns (text_like, exhausted_budget)."""

    remaining = max_read_bytes - counters.bytes_read
    if remaining <= 0:
        return False, True

    probe = min(1024, remaining)
    try:
        with path.open("rb") as handle:
            chunk = handle.read(probe)
    except OSError:
        counters.files_unreadable += 1
        return False, False

    counters.bytes_read += len(chunk)
    if not chunk:
        return True, False
    if b"\x00" in chunk:
        return False, False
    return True, False


def top_level_for(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) == 1:
        return "__root__"
    return parts[0]


def sanitize_shard_name(top_level: str) -> str:
    safe = "".join(ch if (ch.isalnum() or ch in {"-", "_", "."}) else "_" for ch in top_level)
    safe = safe.strip("._")
    if not safe:
        safe = "root"
    return f"{safe}.jsonl"


def iter_repo_files(repo_root: Path, excludes: set[str], counters: RunCounters):
    """Deterministic recursive traversal, symlink-safe and directory-name exclusion based."""

    stack = [repo_root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as handle:
                entries = sorted(handle, key=lambda item: item.name)
        except OSError:
            counters.dirs_skipped += 1
            continue

        child_dirs: list[Path] = []
        child_files: list[Path] = []
        for entry in entries:
            name = entry.name
            if name in {".", ".."}:
                continue
            entry_path = Path(entry.path)
            try:
                if entry.is_symlink():
                    counters.symlinks_skipped += 1
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if name in excludes:
                        counters.dirs_skipped += 1
                        continue
                    child_dirs.append(entry_path)
                    continue
                if entry.is_file(follow_symlinks=False):
                    child_files.append(entry_path)
            except OSError:
                counters.files_unreadable += 1

        for child in reversed(child_dirs):
            stack.append(child)
        for file_path in child_files:
            yield file_path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
            handle.write("\n")


def main() -> int:
    args = parse_args()
    if args.max_files_per_run < 1:
        print("error: --max-files-per-run must be >= 1", file=sys.stderr)
        return 2
    if args.max_seconds < 1:
        print("error: --max-seconds must be >= 1", file=sys.stderr)
        return 2
    if args.max_read_bytes < 0:
        print("error: --max-read-bytes must be >= 0", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        print(f"error: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    index_dir = normalize_index_dir(repo_root, args.index_dir)
    state_path = index_dir / "state.json"
    manifest_path = index_dir / "manifest.json"
    run_path = index_dir / "run.json"
    files_jsonl_path = index_dir / "files.jsonl"
    shards_dir = index_dir / "shards"
    excludes = normalize_excludes(index_dir, args.exclude_dir)

    previous_entries: dict[str, Any] = {}
    fallback_rebuild = False
    fallback_reason = ""
    if args.mode == "incremental":
        previous_entries, fallback_rebuild, fallback_reason = load_state(state_path)

    counters = RunCounters()
    start_wall = time.time()
    start_mono = time.monotonic()
    deadline = start_mono + args.max_seconds

    new_entries: dict[str, Any] = {}
    stop_reason = "completed"
    partial = False

    for file_path in iter_repo_files(repo_root, excludes, counters):
        if counters.files_seen >= args.max_files_per_run:
            partial = True
            stop_reason = "max_files_per_run_reached"
            break
        if time.monotonic() >= deadline:
            partial = True
            stop_reason = "max_seconds_reached"
            break

        counters.files_seen += 1
        rel_path = file_path.relative_to(repo_root).as_posix()

        try:
            st = file_path.stat(follow_symlinks=False)
        except OSError:
            counters.files_unreadable += 1
            continue

        fingerprint = [int(st.st_size), int(st.st_mtime_ns), int(st.st_dev), int(st.st_ino)]
        old = previous_entries.get(rel_path)

        if args.mode == "incremental" and isinstance(old, dict) and old.get("fingerprint") == fingerprint:
            record = old.get("record")
            if isinstance(record, dict):
                counters.files_reused += 1
                new_entries[rel_path] = {"fingerprint": fingerprint, "record": record}
                continue

        ext = Path(rel_path).suffix.lower()
        lang = guess_language(ext)

        if ext in TEXT_EXTS:
            text_like = True
        elif ext in BINARY_EXTS:
            text_like = False
        else:
            text_like, exhausted = is_probably_text(file_path, counters, args.max_read_bytes)
            if exhausted:
                partial = True
                stop_reason = "max_read_bytes_reached"
                break

        record = {
            "path": rel_path,
            "size": int(st.st_size),
            "mtime_ns": int(st.st_mtime_ns),
            "ext": ext,
            "lang": lang,
            "text_like": bool(text_like),
            "top_level": top_level_for(rel_path),
        }

        if rel_path in previous_entries:
            counters.files_updated += 1
        else:
            counters.files_indexed += 1

        new_entries[rel_path] = {"fingerprint": fingerprint, "record": record}

    if partial:
        final_entries = dict(previous_entries)
        final_entries.update(new_entries)
        counters.files_removed = 0
    else:
        final_entries = new_entries
        counters.files_removed = len(set(previous_entries.keys()) - set(new_entries.keys()))

    records = [
        final_entries[path]["record"]
        for path in sorted(final_entries.keys())
        if isinstance(final_entries[path], dict) and isinstance(final_entries[path].get("record"), dict)
    ]

    previous_records = {
        path: payload.get("record")
        for path, payload in previous_entries.items()
        if isinstance(payload, dict) and isinstance(payload.get("record"), dict)
    }
    final_records_by_path = {
        path: payload.get("record")
        for path, payload in final_entries.items()
        if isinstance(payload, dict) and isinstance(payload.get("record"), dict)
    }

    changed_top_levels: set[str] = set()
    for path, record in final_records_by_path.items():
        if previous_records.get(path) != record and isinstance(record, dict):
            changed_top_levels.add(str(record.get("top_level", "__root__")))
    for path in set(previous_records.keys()) - set(final_records_by_path.keys()):
        old = previous_records.get(path)
        if isinstance(old, dict):
            changed_top_levels.add(str(old.get("top_level", "__root__")))

    shard_map: dict[str, str] = {}
    if args.sharded:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            top_level = str(record.get("top_level", "__root__"))
            grouped.setdefault(top_level, []).append(record)

        shards_dir.mkdir(parents=True, exist_ok=True)
        for top_level in sorted(grouped.keys()):
            shard_file = sanitize_shard_name(top_level)
            shard_rel = f"shards/{shard_file}"
            shard_map[top_level] = shard_rel
            shard_path = index_dir / shard_rel
            should_write = (
                args.mode == "full"
                or fallback_rebuild
                or top_level in changed_top_levels
                or not shard_path.is_file()
            )
            if should_write:
                write_jsonl(shard_path, sorted(grouped[top_level], key=lambda item: item["path"]))

        existing_shards = {item.name for item in shards_dir.glob("*.jsonl") if item.is_file()}
        active_shards = {Path(rel).name for rel in shard_map.values()}
        for stale_name in sorted(existing_shards - active_shards):
            try:
                (shards_dir / stale_name).unlink()
            except OSError:
                pass

        if files_jsonl_path.exists():
            try:
                files_jsonl_path.unlink()
            except OSError:
                pass
    else:
        write_jsonl(files_jsonl_path, records)
        if shards_dir.exists() and shards_dir.is_dir():
            for stale in sorted(shards_dir.glob("*.jsonl")):
                try:
                    stale.unlink()
                except OSError:
                    pass

    end_wall = time.time()
    duration = time.monotonic() - start_mono

    run_config = {
        "mode": args.mode,
        "max_files_per_run": args.max_files_per_run,
        "max_seconds": args.max_seconds,
        "max_read_bytes": args.max_read_bytes,
        "exclude_dir": sorted(excludes),
        "sharded": bool(args.sharded),
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": repo_root.as_posix(),
        "generated_at_epoch": int(end_wall),
        "run_config": run_config,
        "counters": counters.to_dict(),
        "storage": {
            "sharded": bool(args.sharded),
            "files_path": None if args.sharded else "files.jsonl",
            "shard_map": shard_map,
        },
    }

    state = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": repo_root.as_posix(),
        "updated_at_epoch": int(end_wall),
        "entries": final_entries,
    }

    status = "partial" if partial else "ok"
    run_report = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "stop_reason": stop_reason,
        "started_at_epoch": int(start_wall),
        "finished_at_epoch": int(end_wall),
        "duration_seconds": round(duration, 3),
        "fallback_rebuild": fallback_rebuild,
        "fallback_reason": fallback_reason,
        "budgets": {
            "max_files_per_run": args.max_files_per_run,
            "max_seconds": args.max_seconds,
            "max_read_bytes": args.max_read_bytes,
        },
        "usage": {
            "files_seen": counters.files_seen,
            "bytes_read": counters.bytes_read,
            "seconds_elapsed": round(duration, 3),
        },
        "counters": counters.to_dict(),
        "storage": {
            "sharded": bool(args.sharded),
            "record_count": len(records),
            "scope_count": len(shard_map) if args.sharded else 1,
        },
    }

    index_dir.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    write_json(state_path, state)
    write_json(run_path, run_report)

    if args.json_out:
        out_path = Path(args.json_out).expanduser()
        if not out_path.is_absolute():
            out_path = (repo_root / out_path).resolve()
        write_json(out_path, run_report)

    print(
        f"status={status} stop_reason={stop_reason} files_seen={counters.files_seen} "
        f"records={len(records)} bytes_read={counters.bytes_read} sharded={args.sharded}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
