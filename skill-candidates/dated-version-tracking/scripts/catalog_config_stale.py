#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - Python 3.11+ expected
    raise SystemExit(f"Python 3.11+ required for tomllib: {exc}")


CURRENT_BUCKET = "Current Config"
PAST_GOOD_BUCKET = "Past Good Configs"
BROKEN_BUCKET = "Broken Configs"
BROKEN_ARTIFACT_PATTERNS = (
    ".codex-global-state*.broken*",
    "logs_*.sqlite.broken",
)
BROKEN_ARTIFACT_DIRS = (
    ".sandbox.broken",
)
LIVE_SAFETY_EXCLUSIONS = (
    "auth.json",
    "config.toml",
    "state_*.sqlite*",
    "logs_*.sqlite",
    "*.sqlite-wal",
    "*.sqlite-shm",
    "sessions",
    "logs",
    ".sandbox",
)
FORBIDDEN_TOP_LEVEL_KEYS = {
    "model_provider",
    "model_providers",
    "background_terminal_max_timeout",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_name(path: Path) -> str:
    return path.name.replace(":", "_").replace("\\", "_").replace("/", "_")


def _unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    for idx in range(1, 1000):
        candidate = parent / f"{stem}__dup{idx}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find unique destination for {dest}")


def _copy_or_move(source: Path, dest: Path, *, move: bool, dry_run: bool) -> dict[str, Any]:
    dest = _unique_dest(dest)
    action = "move" if move else "copy"
    result = {
        "action": action,
        "source": str(source),
        "destination": str(dest),
        "dry_run": dry_run,
    }
    if dry_run:
        return result
    dest.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(source), str(dest))
    else:
        shutil.copy2(source, dest)
    return result


def _broken_artifacts(codex_home: Path) -> list[Path]:
    artifacts: list[Path] = []
    for pattern in BROKEN_ARTIFACT_PATTERNS:
        artifacts.extend(path for path in codex_home.glob(pattern) if path.exists())
    for dirname in BROKEN_ARTIFACT_DIRS:
        path = codex_home / dirname
        if path.exists():
            artifacts.append(path)
    return sorted(set(artifacts), key=lambda path: path.name)


def _load_live_config(codex_home: Path) -> tuple[dict[str, Any] | None, list[str]]:
    live_path = codex_home / "config.toml"
    issues: list[str] = []
    if not live_path.exists():
        return None, ["live config missing"]
    try:
        data = tomllib.loads(live_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"live config parse failed: {exc}"]
    expected = {
        "model": "gpt-5.5",
        "review_model": "gpt-5.5",
        "model_reasoning_effort": "xhigh",
        "profile": "starframe",
    }
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            issues.append(f"live {key} expected {expected_value}, got {data.get(key)}")
    features = data.get("features")
    if not isinstance(features, dict) or features.get("shell_snapshot") is not False:
        issues.append("live features.shell_snapshot must be false")
    for key in sorted(FORBIDDEN_TOP_LEVEL_KEYS):
        if key in data:
            issues.append(f"live config has forbidden key {key}")
    for name, server in (data.get("mcp_servers") or {}).items():
        if isinstance(server, dict) and server.get("required") is True:
            issues.append(f"live MCP server {name} is required=true")
    return data, issues


def _preflight(codex_home: Path, stale_root: Path, *, include_broken_artifacts: bool) -> list[str]:
    issues: list[str] = []
    if not codex_home.exists():
        issues.append(f"codex_home does not exist: {codex_home}")
    live_data, live_issues = _load_live_config(codex_home)
    issues.extend(live_issues)
    if live_data is None:
        return issues
    if stale_root.resolve() == codex_home.resolve():
        issues.append("stale_root cannot be codex_home")
    if include_broken_artifacts and (codex_home / ".sandbox").exists():
        # Current .sandbox is explicitly protected. This check documents that only .sandbox.broken is eligible.
        pass
    return issues


def _stale_hits(text: str) -> list[str]:
    needles = (
        "gpt-5.4",
        "Main Codex lane must start on gpt-5.4",
        "model_provider",
        "model_providers",
        "openai-long-timeout",
        "background_terminal_max_timeout",
        "chat.mcp.autoStart",
    )
    return [needle for needle in needles if needle in text]


def _classify(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    record: dict[str, Any] = {
        "name": path.name,
        "source_path": str(path),
        "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "length": path.stat().st_size,
        "sha256": _sha256(path),
        "parse_ok": False,
        "bucket": PAST_GOOD_BUCKET,
        "usable_now": False,
        "reasons": [],
        "stale_hits": _stale_hits(text),
        "model": None,
        "review_model": None,
        "model_reasoning_effort": None,
        "profile": None,
        "analytics_enabled": None,
        "shell_snapshot": None,
        "required_true_mcp": [],
        "forbidden_keys": [],
    }
    try:
        data = tomllib.loads(text)
    except Exception as exc:
        record["bucket"] = BROKEN_BUCKET
        record["reasons"].append(f"toml_parse_failed: {exc}")
        return record

    record["parse_ok"] = True
    record["model"] = data.get("model")
    record["review_model"] = data.get("review_model")
    record["model_reasoning_effort"] = data.get("model_reasoning_effort")
    record["profile"] = data.get("profile")
    analytics = data.get("analytics")
    if isinstance(analytics, dict):
        record["analytics_enabled"] = analytics.get("enabled")
    features = data.get("features")
    if isinstance(features, dict):
        record["shell_snapshot"] = features.get("shell_snapshot")

    for key in ("model_provider", "model_providers", "background_terminal_max_timeout"):
        if key in data:
            record["forbidden_keys"].append(key)
    for name, server in (data.get("mcp_servers") or {}).items():
        if isinstance(server, dict) and server.get("required") is True:
            record["required_true_mcp"].append(name)

    if path.name == "config.toml":
        record["bucket"] = CURRENT_BUCKET
        expected = {
            "model": "gpt-5.5",
            "review_model": "gpt-5.5",
            "model_reasoning_effort": "xhigh",
            "profile": "starframe",
        }
        for key, expected_value in expected.items():
            if record.get(key) != expected_value:
                record["reasons"].append(f"current_{key}_drift: expected {expected_value}, got {record.get(key)}")
        if record["required_true_mcp"]:
            record["reasons"].append("current_has_required_true_mcp")
        if record["forbidden_keys"]:
            record["reasons"].append("current_has_forbidden_keys")
        if record["stale_hits"]:
            record["reasons"].append("current_has_stale_hits")
        if record["shell_snapshot"] is not False:
            record["reasons"].append("current_shell_snapshot_not_false")
        record["usable_now"] = not record["reasons"]
        if not record["usable_now"]:
            record["bucket"] = BROKEN_BUCKET
        return record

    name_lower = path.name.lower()
    if ".fail" in name_lower or name_lower.endswith(".broken"):
        record["bucket"] = BROKEN_BUCKET
        record["reasons"].append("filename_marks_failed_or_broken")
    if record["forbidden_keys"]:
        record["bucket"] = BROKEN_BUCKET
        record["reasons"].append("forbidden_config_keys")
    if record["model_reasoning_effort"] not in (None, "xhigh"):
        record["bucket"] = BROKEN_BUCKET
        record["reasons"].append("reasoning_not_xhigh")
    if record["required_true_mcp"]:
        record["reasons"].append("historical_required_true_mcp")
    if "gpt-5.4" in record["stale_hits"]:
        record["reasons"].append("historical_gpt_5_4_stale_after_2026_04_23")
    if not record["reasons"]:
        record["reasons"].append("parseable_historical_backup")
    return record


def catalog(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home).expanduser()
    stale_root = Path(args.stale_root).expanduser() if args.stale_root else codex_home / "config.stale"
    preflight_issues = _preflight(codex_home, stale_root, include_broken_artifacts=args.include_broken_artifacts)
    if args.require_preflight and preflight_issues:
        for issue in preflight_issues:
            print(f"preflight failed: {issue}")
        return 1
    files = sorted(
        [path for path in codex_home.iterdir() if path.is_file() and path.name.startswith("config.toml")],
        key=lambda path: (path.stat().st_mtime, path.name),
    )
    records = [_classify(path) for path in files]
    operation = "organize_move" if args.organize else "materialize_copy" if args.materialize else "scan_only"
    manifest = {
        "schema_version": 1,
        "generated_at": _now(),
        "codex_home": str(codex_home),
        "stale_root": str(stale_root),
        "live_config": str(codex_home / "config.toml"),
        "operation": operation,
        "dry_run": args.dry_run,
        "copy_only": not args.organize,
        "preflight_required": args.require_preflight,
        "preflight_issues": preflight_issues,
        "live_safety_exclusions": LIVE_SAFETY_EXCLUSIONS,
        "bucket_contract": {
            CURRENT_BUCKET: "Current live config snapshot copied for comparison only.",
            PAST_GOOD_BUCKET: "Parseable historical backups. May be stale and must not be promoted without validation.",
            BROKEN_BUCKET: "Failed, forbidden, malformed, or known-bad configs retained as regression evidence.",
        },
        "records": records,
        "file_actions": [],
        "broken_artifacts": [],
    }
    if args.materialize or args.organize:
        stale_root.mkdir(parents=True, exist_ok=True)
        for bucket in (CURRENT_BUCKET, PAST_GOOD_BUCKET, BROKEN_BUCKET):
            (stale_root / bucket).mkdir(exist_ok=True)
        for record in records:
            source = Path(record["source_path"])
            dest = stale_root / record["bucket"] / _safe_name(source)
            move = args.organize and source.name != "config.toml"
            action = _copy_or_move(source, dest, move=move, dry_run=args.dry_run)
            manifest["file_actions"].append(action)
            record["catalog_path"] = action["destination"]
        if args.include_broken_artifacts:
            for artifact in _broken_artifacts(codex_home):
                dest = stale_root / BROKEN_BUCKET / _safe_name(artifact)
                action = _copy_or_move(artifact, dest, move=args.organize, dry_run=args.dry_run)
                action["artifact_kind"] = "directory" if artifact.is_dir() else "file"
                manifest["broken_artifacts"].append(action)
        manifest_path = stale_root / "manifest.json"
        if not args.dry_run:
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"wrote {manifest_path}")
        else:
            print(json.dumps(manifest, indent=2, sort_keys=True))
    summary: dict[str, int] = {}
    for record in records:
        summary[record["bucket"]] = summary.get(record["bucket"], 0) + 1
    print(json.dumps({"records": len(records), "summary": summary, "current_usable": any(r["name"] == "config.toml" and r["usable_now"] for r in records)}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog Codex config backups into config.stale buckets.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--stale-root")
    parser.add_argument("--materialize", action="store_true", help="Copy config files into bucket folders and write manifest.json.")
    parser.add_argument("--organize", action="store_true", help="Copy live config, then move non-live config.toml* files into bucket folders.")
    parser.add_argument("--include-broken-artifacts", action="store_true", help="Also move explicitly broken non-live artifacts such as *.broken files and .sandbox.broken.")
    parser.add_argument("--dry-run", action="store_true", help="Print intended actions without changing files.")
    parser.add_argument("--require-preflight", action="store_true", help="Refuse write/move operations unless live config and safety gates pass.")
    return catalog(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
