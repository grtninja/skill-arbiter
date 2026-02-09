#!/usr/bin/env python3
"""Query metadata-only index artifacts produced by index_build.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

DEFAULT_LIMIT = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query local codex index artifacts")
    parser.add_argument("--index-dir", default=".codex-index", help="Path to index directory")
    parser.add_argument("--path-contains", default="", help="Substring filter on relative path")
    parser.add_argument("--ext", default="", help="Extension filter, e.g. .py or py")
    parser.add_argument("--lang", default="", help="Language filter, e.g. python")
    parser.add_argument("--min-size", type=int, default=-1, help="Minimum file size in bytes")
    parser.add_argument("--max-size", type=int, default=-1, help="Maximum file size in bytes")
    parser.add_argument(
        "--changed-since-epoch",
        type=int,
        default=-1,
        help="Filter files with mtime >= epoch seconds",
    )
    parser.add_argument(
        "--scope",
        default="all",
        help="Top-level scope for sharded indexes; use 'all' for full index",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum rows to output")
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format",
    )
    return parser.parse_args()


def normalize_ext(value: str) -> str:
    value = value.strip().lower()
    if not value:
        return ""
    if value.startswith("."):
        return value
    return f".{value}"


def load_manifest(index_dir: Path) -> dict[str, Any]:
    path = index_dir / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def record_paths(index_dir: Path, manifest: dict[str, Any], scope: str) -> list[Path]:
    storage = manifest.get("storage", {})
    sharded = bool(storage.get("sharded", False))
    if sharded:
        shard_map = storage.get("shard_map", {})
        if not isinstance(shard_map, dict):
            return []
        if scope != "all":
            shard_rel = shard_map.get(scope)
            if not isinstance(shard_rel, str):
                return []
            return [index_dir / shard_rel]
        paths = []
        for top_level in sorted(shard_map.keys()):
            shard_rel = shard_map[top_level]
            if isinstance(shard_rel, str):
                paths.append(index_dir / shard_rel)
        return paths

    files_rel = storage.get("files_path")
    if isinstance(files_rel, str) and files_rel:
        return [index_dir / files_rel]
    return [index_dir / "files.jsonl"]


def matches_filters(record: dict[str, Any], args: argparse.Namespace, ext_filter: str, scope: str) -> bool:
    path = str(record.get("path", ""))
    ext = str(record.get("ext", "")).lower()
    lang = str(record.get("lang", "")).lower()
    top_level = str(record.get("top_level", ""))

    try:
        size = int(record.get("size", -1))
        mtime_ns = int(record.get("mtime_ns", -1))
    except (TypeError, ValueError):
        return False

    if args.path_contains and args.path_contains.lower() not in path.lower():
        return False
    if ext_filter and ext != ext_filter:
        return False
    if args.lang and lang != args.lang.strip().lower():
        return False
    if args.min_size >= 0 and size < args.min_size:
        return False
    if args.max_size >= 0 and size > args.max_size:
        return False
    if args.changed_since_epoch >= 0:
        if mtime_ns < args.changed_since_epoch * 1_000_000_000:
            return False
    if scope != "all" and top_level != scope:
        return False
    return True


def render_table(rows: list[dict[str, Any]]) -> str:
    headers = ["path", "size", "ext", "lang", "top_level", "mtime_ns", "text_like"]
    width: dict[str, int] = {key: len(key) for key in headers}

    for row in rows:
        for key in headers:
            width[key] = max(width[key], len(str(row.get(key, ""))))

    def row_line(row: dict[str, Any]) -> str:
        return "  ".join(str(row.get(key, "")).ljust(width[key]) for key in headers)

    sep = "  ".join("-" * width[key] for key in headers)
    lines = [row_line({key: key for key in headers}), sep]
    for row in rows:
        lines.append(row_line(row))
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        print("error: --limit must be >= 1", file=sys.stderr)
        return 2
    if args.min_size >= 0 and args.max_size >= 0 and args.min_size > args.max_size:
        print("error: --min-size cannot be greater than --max-size", file=sys.stderr)
        return 2

    index_dir = Path(args.index_dir).expanduser().resolve()
    if not index_dir.is_dir():
        print(f"error: index dir not found: {index_dir}", file=sys.stderr)
        return 2

    try:
        manifest = load_manifest(index_dir)
    except (OSError, FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    scope = args.scope.strip() or "all"
    ext_filter = normalize_ext(args.ext)

    rows: list[dict[str, Any]] = []
    for path in record_paths(index_dir, manifest, scope):
        for record in iter_jsonl(path):
            if not matches_filters(record, args, ext_filter, scope):
                continue
            rows.append(
                {
                    "path": str(record.get("path", "")),
                    "size": int(record.get("size", 0)),
                    "ext": str(record.get("ext", "")),
                    "lang": str(record.get("lang", "")),
                    "top_level": str(record.get("top_level", "")),
                    "mtime_ns": int(record.get("mtime_ns", 0)),
                    "text_like": bool(record.get("text_like", False)),
                }
            )

    rows.sort(key=lambda item: item["path"])
    rows = rows[: args.limit]

    if args.format == "json":
        payload = {
            "count": len(rows),
            "scope": scope,
            "limit": args.limit,
            "results": rows,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0

    print(render_table(rows))
    print(f"rows={len(rows)} scope={scope} limit={args.limit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
