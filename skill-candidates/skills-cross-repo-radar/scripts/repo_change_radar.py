#!/usr/bin/env python3
"""Build a bounded cross-repo change radar report."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_MARKERS = {
    "AGENTS.md",
    "BOUNDARIES.md",
    "README.md",
    "HEARTBEAT.md",
    "CONTRIBUTING.md",
}

CONTRACT_HINTS = (
    "manifest",
    "schema",
    "contract",
    "api",
    "endpoint",
    "bridge",
    "orchestr",
    "policy",
)

SKILL_HINTS = (
    "skill",
    "arbiter",
    "codex",
    ".codex",
    "agent",
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _run_git(repo_path: Path, args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)
    text = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode, text


def _parse_repo_arg(text: str) -> tuple[str, Path]:
    raw = str(text or "").strip()
    if "=" not in raw:
        raise ValueError(f"invalid --repo {raw!r}, expected name=path")
    name, path_text = raw.split("=", 1)
    name = name.strip()
    path = Path(path_text.strip()).expanduser().resolve()
    if not name:
        raise ValueError(f"invalid --repo {raw!r}, missing repo name")
    return name, path


def _classify_paths(paths: list[str]) -> dict[str, Any]:
    policy_hits: list[str] = []
    contract_hits: list[str] = []
    skill_hits: list[str] = []

    for rel in paths:
        base = Path(rel).name
        low = rel.lower()
        if base in POLICY_MARKERS or "/docs/" in low or "\\docs\\" in low:
            policy_hits.append(rel)
        if any(token in low for token in CONTRACT_HINTS):
            contract_hits.append(rel)
        if any(token in low for token in SKILL_HINTS):
            skill_hits.append(rel)

    return {
        "policy_paths": sorted(set(policy_hits)),
        "contract_paths": sorted(set(contract_hits)),
        "skill_paths": sorted(set(skill_hits)),
    }


def build_repo_row(name: str, repo_path: Path, since_days: int, file_limit: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "repo": name,
        "path": str(repo_path),
        "exists": repo_path.exists(),
        "git_repo": (repo_path / ".git").exists(),
        "ok": False,
        "blockers": [],
    }
    if not row["exists"]:
        row["blockers"].append("repo path missing")
        return row
    if not row["git_repo"]:
        row["blockers"].append("not a git repository")
        return row

    last_rc, last_out = _run_git(repo_path, ["log", "-1", "--date=iso-strict", "--format=%H|%cI|%s"])
    commits_rc, commits_out = _run_git(repo_path, ["log", f"--since={since_days}.days", "--format=%H|%cI|%an|%s"])
    files_rc, files_out = _run_git(repo_path, ["log", f"--since={since_days}.days", "--name-only", "--pretty=format:"])
    status_rc, status_out = _run_git(repo_path, ["status", "--porcelain"])

    if last_rc != 0:
        row["blockers"].append(f"git log -1 failed: {last_out}")
        return row
    if commits_rc != 0:
        row["blockers"].append(f"git log --since failed: {commits_out}")
        return row
    if files_rc != 0:
        row["blockers"].append(f"git log --name-only failed: {files_out}")
        return row
    if status_rc != 0:
        row["blockers"].append(f"git status failed: {status_out}")
        return row

    row["ok"] = True

    last_parts = last_out.split("|", 2)
    row["last_commit"] = {
        "hash": last_parts[0][:12] if len(last_parts) > 0 else "",
        "timestamp": last_parts[1] if len(last_parts) > 1 else "",
        "subject": last_parts[2] if len(last_parts) > 2 else "",
    }

    commits: list[dict[str, str]] = []
    for line in commits_out.splitlines():
        item = line.strip()
        if not item:
            continue
        parts = item.split("|", 3)
        if len(parts) < 4:
            continue
        commits.append(
            {
                "hash": parts[0][:12],
                "timestamp": parts[1],
                "author": parts[2],
                "subject": parts[3],
            }
        )

    changed_files = [line.strip() for line in files_out.splitlines() if line.strip()]
    changed_files = sorted(set(changed_files))
    changed_files_sample = changed_files[: max(file_limit, 1)]
    dirty_files = [line.strip() for line in status_out.splitlines() if line.strip()]

    classes = _classify_paths(changed_files)
    row.update(
        {
            "window_days": since_days,
            "commit_count": len(commits),
            "commits_sample": commits[:25],
            "changed_files_count": len(changed_files),
            "changed_files_sample": changed_files_sample,
            "dirty_files_count": len(dirty_files),
            "dirty_files_sample": dirty_files[:25],
            "policy_change_count": len(classes["policy_paths"]),
            "contract_change_count": len(classes["contract_paths"]),
            "skill_change_count": len(classes["skill_paths"]),
            "policy_paths": classes["policy_paths"][:50],
            "contract_paths": classes["contract_paths"][:50],
            "skill_paths": classes["skill_paths"][:50],
            "risk_flags": sorted(
                set(
                    [
                        *(["policy_sensitive"] if classes["policy_paths"] else []),
                        *(["contract_surface"] if classes["contract_paths"] else []),
                        *(["skill_system"] if classes["skill_paths"] else []),
                        *(["dirty_worktree"] if dirty_files else []),
                    ]
                )
            ),
        }
    )
    return row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate recent cross-repo radar report")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Repository mapping in name=path format (repeatable)",
    )
    parser.add_argument("--since-days", type=int, default=14, help="Lookback window in days")
    parser.add_argument("--file-limit", type=int, default=200, help="Max changed files to keep in sample")
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def render_table(payload: dict[str, Any]) -> str:
    rows = payload.get("repos", [])
    lines = [
        f"generated_at: {payload.get('generated_at')}",
        f"window_days: {payload.get('window_days')}",
        f"repo_count: {len(rows)}",
        "",
        "repo                          commits  files  policy  contract  skills  dirty  flags",
        "----------------------------  -------  -----  ------  --------  ------  -----  --------------------------",
    ]
    for row in rows:
        flags = ",".join(row.get("risk_flags", [])) or "-"
        lines.append(
            "{repo:<28}  {commits:>7}  {files:>5}  {policy:>6}  {contract:>8}  {skills:>6}  {dirty:>5}  {flags}".format(
                repo=str(row.get("repo", ""))[:28],
                commits=int(row.get("commit_count", 0) or 0),
                files=int(row.get("changed_files_count", 0) or 0),
                policy=int(row.get("policy_change_count", 0) or 0),
                contract=int(row.get("contract_change_count", 0) or 0),
                skills=int(row.get("skill_change_count", 0) or 0),
                dirty=int(row.get("dirty_files_count", 0) or 0),
                flags=flags,
            )
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    since_days = max(int(args.since_days), 1)
    file_limit = max(int(args.file_limit), 1)

    blockers: list[str] = []
    repos: list[tuple[str, Path]] = []
    for item in args.repo:
        try:
            repos.append(_parse_repo_arg(item))
        except ValueError as exc:
            blockers.append(str(exc))
    if not repos:
        blockers.append("at least one --repo name=path argument is required")

    payload: dict[str, Any] = {
        "pass": not blockers,
        "generated_at": _now_iso(),
        "window_days": since_days,
        "blockers": blockers,
        "repos": [],
    }
    if blockers:
        if args.format == "json":
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print("\n".join(["blockers:"] + [f"- {item}" for item in blockers]))
        if args.json_out:
            out = Path(args.json_out).expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return 1

    rows: list[dict[str, Any]] = []
    for name, repo_path in repos:
        rows.append(build_repo_row(name, repo_path, since_days, file_limit))
    payload["repos"] = rows

    row_blockers = []
    for row in rows:
        if row.get("blockers"):
            row_blockers.append({"repo": row.get("repo"), "blockers": row.get("blockers")})
    if row_blockers:
        payload["pass"] = False
        payload["blockers"].extend([f"{item['repo']}: {', '.join(item['blockers'])}" for item in row_blockers])

    payload["summary"] = {
        "repos_total": len(rows),
        "repos_ok": sum(1 for row in rows if row.get("ok")),
        "repos_with_policy_changes": sum(1 for row in rows if int(row.get("policy_change_count", 0) or 0) > 0),
        "repos_with_contract_changes": sum(1 for row in rows if int(row.get("contract_change_count", 0) or 0) > 0),
        "repos_with_skill_changes": sum(1 for row in rows if int(row.get("skill_change_count", 0) or 0) > 0),
        "repos_dirty": sum(1 for row in rows if int(row.get("dirty_files_count", 0) or 0) > 0),
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(render_table(payload))

    if args.json_out:
        out = Path(args.json_out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return 0 if payload.get("pass", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())

