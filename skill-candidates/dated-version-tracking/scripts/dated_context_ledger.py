#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


SCHEMA_VERSION = 1
VALID_KINDS = {
    "version_assumption",
    "dependency_assumption",
    "context_request",
    "context_fact",
    "stale_check",
}
VALID_STATUS = {"active", "unverified", "stale", "superseded", "rejected"}
VALID_CONFIDENCE = {"high", "medium", "low"}
DEFAULT_LEDGER = Path.home() / ".codex" / "workstreams" / "dated-version-context-ledger.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ledger_path(raw: str | None) -> Path:
    env_path = os.environ.get("CODEX_DATED_CONTEXT_LEDGER")
    return Path(raw or env_path or DEFAULT_LEDGER).expanduser()


def _parse_temporal(value: str, field: str) -> None:
    candidate = value.strip()
    if not candidate:
        raise ValueError(f"{field} is empty")
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        datetime.fromisoformat(candidate)
        return
    except ValueError:
        pass
    try:
        datetime.fromisoformat(candidate + "T00:00:00+00:00")
        return
    except ValueError as exc:
        raise ValueError(f"{field} is not ISO 8601: {value}") from exc


def _as_list(values: list[str] | None) -> list[str]:
    return [item for item in values or [] if item]


def _record_id(record: dict[str, Any]) -> str:
    seed = json.dumps(
        {
            "kind": record.get("kind"),
            "subject": record.get("subject"),
            "claim": record.get("claim"),
            "source_time": record.get("source_time"),
            "recorded_at": record.get("recorded_at"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    issues: list[str] = []
    if not path.exists():
        return records, issues
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(f"{path}:{line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(value, dict):
                issues.append(f"{path}:{line_no}: record is not an object")
                continue
            records.append(value)
    return records, issues


def validate_record(record: dict[str, Any], line_no: int | None = None) -> list[str]:
    prefix = f"line {line_no}: " if line_no else ""
    issues: list[str] = []
    required = (
        "schema_version",
        "record_id",
        "kind",
        "recorded_at",
        "subject",
        "claim",
        "source",
        "source_time",
        "status",
        "confidence",
        "freshness_rule",
    )
    for field in required:
        if field not in record or record[field] in ("", None):
            issues.append(f"{prefix}missing {field}")

    if record.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"{prefix}schema_version must be {SCHEMA_VERSION}")
    if record.get("kind") not in VALID_KINDS:
        issues.append(f"{prefix}kind must be one of {sorted(VALID_KINDS)}")
    if record.get("status") not in VALID_STATUS:
        issues.append(f"{prefix}status must be one of {sorted(VALID_STATUS)}")
    if record.get("confidence") not in VALID_CONFIDENCE:
        issues.append(f"{prefix}confidence must be one of {sorted(VALID_CONFIDENCE)}")

    for field in ("recorded_at", "source_time", "effective_date", "verified_date", "refresh_after", "expires_at", "requested_at"):
        value = record.get(field)
        if isinstance(value, str) and value:
            try:
                _parse_temporal(value, field)
            except ValueError as exc:
                issues.append(f"{prefix}{exc}")

    kind = record.get("kind")
    if kind in {"version_assumption", "dependency_assumption"}:
        for field in ("effective_date", "verified_date", "evidence", "stale_if"):
            if field not in record or record[field] in ("", None, []):
                issues.append(f"{prefix}{kind} missing {field}")
        if not (record.get("refresh_after") or record.get("expires_at")):
            issues.append(f"{prefix}{kind} needs refresh_after or expires_at")
    if kind in {"context_request", "context_fact"} and not record.get("requested_at"):
        issues.append(f"{prefix}{kind} missing requested_at")

    resolved = record.get("resolved_time_reference")
    if resolved is not None:
        if not isinstance(resolved, dict):
            issues.append(f"{prefix}resolved_time_reference must be an object")
        else:
            for field in ("raw", "resolved_start"):
                if not resolved.get(field):
                    issues.append(f"{prefix}resolved_time_reference missing {field}")

    return issues


def validate_ledger(path: Path) -> int:
    records, issues = _read_jsonl(path)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    issues.extend(validate_record(record, line_no))
    duplicate_ids = sorted(
        record_id
        for record_id in {record.get("record_id") for record in records}
        if record_id and sum(1 for record in records if record.get("record_id") == record_id) > 1
    )
    for record_id in duplicate_ids:
        issues.append(f"duplicate record_id: {record_id}")

    if issues:
        for issue in issues:
            print(issue)
        return 1
    print(f"valid ledger: {path} ({len(records)} record(s))")
    return 0


def append_record(args: argparse.Namespace) -> int:
    path = _ledger_path(args.ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    recorded_at = args.recorded_at or _now()
    source_time = args.source_time or recorded_at
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": args.kind,
        "recorded_at": recorded_at,
        "subject": args.subject,
        "claim": args.claim,
        "source": args.source,
        "source_time": source_time,
        "status": args.status,
        "confidence": args.confidence,
        "freshness_rule": args.freshness_rule,
    }
    optional_scalars = (
        "effective_date",
        "verified_date",
        "refresh_after",
        "expires_at",
        "requested_at",
        "valid_until",
        "supersedes",
        "notes",
    )
    for field in optional_scalars:
        value = getattr(args, field, None)
        if value:
            record[field] = value
    evidence = _as_list(args.evidence)
    stale_if = _as_list(args.stale_if)
    if evidence:
        record["evidence"] = evidence
    if stale_if:
        record["stale_if"] = stale_if
    if args.resolved_time_raw:
        record["resolved_time_reference"] = {
            "raw": args.resolved_time_raw,
            "resolved_start": args.resolved_time_start,
            "resolved_end": args.resolved_time_end,
        }
    record["record_id"] = args.record_id or _record_id(record)
    issues = validate_record(record)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"appended {record['record_id']} to {path}")
    return 0


def scan_paths(args: argparse.Namespace) -> int:
    patterns = _as_list(args.pattern)
    allowed = _as_list(args.allow_path_fragment)
    if not patterns:
        print("scan requires at least one --pattern", file=sys.stderr)
        return 2
    roots = [Path(item) for item in args.path]
    hits: list[str] = []
    for root in roots:
        files = [root]
        if root.is_dir():
            files = [item for item in root.rglob("*") if item.is_file()]
        for file_path in files:
            path_text = str(file_path)
            if allowed and any(fragment in path_text for fragment in allowed):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                hits.append(f"{file_path}: unreadable: {exc}")
                continue
            for pattern in patterns:
                if pattern in text:
                    hits.append(f"{file_path}: contains {pattern!r}")
    if hits:
        for hit in hits:
            print(hit)
        return 1
    print("no stale pattern hits")
    return 0


def summary(args: argparse.Namespace) -> int:
    path = _ledger_path(args.ledger)
    records, issues = _read_jsonl(path)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    counts: dict[str, int] = {}
    for record in records:
        key = f"{record.get('kind', 'unknown')}:{record.get('status', 'unknown')}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"ledger": str(path), "records": len(records), "counts": counts}, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain the dated version/context JSONL ledger.")
    parser.add_argument("--ledger", help="Ledger path. Defaults to CODEX_DATED_CONTEXT_LEDGER or the STARFRAME workstream ledger.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="Append one validated ledger record.")
    append.add_argument("--kind", required=True, choices=sorted(VALID_KINDS))
    append.add_argument("--record-id")
    append.add_argument("--recorded-at")
    append.add_argument("--subject", required=True)
    append.add_argument("--claim", required=True)
    append.add_argument("--source", required=True)
    append.add_argument("--source-time")
    append.add_argument("--status", default="active", choices=sorted(VALID_STATUS))
    append.add_argument("--confidence", default="high", choices=sorted(VALID_CONFIDENCE))
    append.add_argument("--freshness-rule", required=True)
    append.add_argument("--effective-date")
    append.add_argument("--verified-date")
    append.add_argument("--refresh-after")
    append.add_argument("--expires-at")
    append.add_argument("--requested-at")
    append.add_argument("--valid-until")
    append.add_argument("--supersedes")
    append.add_argument("--notes")
    append.add_argument("--evidence", action="append")
    append.add_argument("--stale-if", action="append")
    append.add_argument("--resolved-time-raw")
    append.add_argument("--resolved-time-start")
    append.add_argument("--resolved-time-end")
    append.set_defaults(func=append_record)

    validate = subparsers.add_parser("validate", help="Validate the ledger.")
    validate.set_defaults(func=lambda args: validate_ledger(_ledger_path(args.ledger)))

    scan = subparsers.add_parser("scan", help="Scan files for literal stale patterns.")
    scan.add_argument("--path", action="append", required=True)
    scan.add_argument("--pattern", action="append", required=True)
    scan.add_argument("--allow-path-fragment", action="append")
    scan.set_defaults(func=scan_paths)

    summary_parser = subparsers.add_parser("summary", help="Print ledger counts.")
    summary_parser.set_defaults(func=summary)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
