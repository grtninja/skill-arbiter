#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def run_gh(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["gh", *args],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"gh {' '.join(args)} failed")
    return proc.stdout


def collect_pr_evidence(repo: Path, pr_numbers: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in pr_numbers:
        number = str(raw).strip()
        if not number:
            continue
        try:
            payload = json.loads(
                run_gh(
                    repo,
                    "pr",
                    "view",
                    number,
                    "--json",
                    "number,title,state,isDraft,headRefName,baseRefName,headRefOid,createdAt,mergedAt,url",
                )
            )
        except Exception as exc:  # pragma: no cover - best-effort evidence lane
            rows.append({"number": number, "error": str(exc)})
            continue
        rows.append(payload)
    return rows


def collect_run_evidence(repo: Path, run_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in run_ids:
        run_id = str(raw).strip()
        if not run_id:
            continue
        try:
            payload = json.loads(
                run_gh(
                    repo,
                    "run",
                    "view",
                    run_id,
                    "--json",
                    "databaseId,workflowName,displayTitle,headBranch,headSha,status,conclusion,createdAt,updatedAt,event,url",
                )
            )
        except Exception as exc:  # pragma: no cover - best-effort evidence lane
            rows.append({"run_id": run_id, "error": str(exc)})
            continue
        rows.append(payload)
    return rows


def parse_commit_log(raw: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in raw.splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        commit, authored_at, subject, touched = parts
        touched_paths = [item for item in touched.split("\x1f") if item]
        rows.append(
            {
                "commit": commit,
                "authored_at": authored_at,
                "subject": subject,
                "touched_paths": touched_paths,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect rollback-regression triage evidence.")
    parser.add_argument("--repo", required=True, help="Target git repo")
    parser.add_argument("--good-commit", required=True, help="Last-known-good commit")
    parser.add_argument("--compare-ref", default="HEAD", help="Ref to compare against")
    parser.add_argument("--focus-path", action="append", default=[], help="Repeatable path filter")
    parser.add_argument("--gh-pr", action="append", default=[], help="Optional PR number to collect via gh")
    parser.add_argument("--gh-run", action="append", default=[], help="Optional GitHub Actions run id to collect via gh")
    parser.add_argument("--max-commits", type=int, default=30, help="Maximum post-anchor commits to emit")
    parser.add_argument("--json-out", help="Write JSON output to this path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise SystemExit(f"Repo does not exist: {repo}")

    pathspec = args.focus_path or []
    log_args = [
        "log",
        "--reverse",
        f"{args.good_commit}..{args.compare_ref}",
        "--date=iso-strict",
        "--pretty=format:%H\t%ad\t%s\t",
        "--name-only",
    ]
    if pathspec:
        log_args.append("--")
        log_args.extend(pathspec)

    log_output = run_git(repo, *log_args)
    commit_blocks = []
    current_commit = None
    current_paths: list[str] = []
    for line in log_output.splitlines():
        if "\t" in line and len(line.split("\t")) >= 4:
            if current_commit:
                current_commit["touched_paths"] = current_paths
                commit_blocks.append(current_commit)
            commit, authored_at, subject, _ = line.split("\t", 3)
            current_commit = {
                "commit": commit,
                "authored_at": authored_at,
                "subject": subject,
            }
            current_paths = []
        elif current_commit and line.strip():
            current_paths.append(line.strip())
    if current_commit:
        current_commit["touched_paths"] = current_paths
        commit_blocks.append(current_commit)

    commit_blocks = commit_blocks[: max(args.max_commits, 1)]

    for row in commit_blocks:
        commit = str(row["commit"])
        contains_raw = run_git(
            repo,
            "for-each-ref",
            "refs/remotes",
            "--contains",
            commit,
            "--format=%(refname:short)",
        )
        row["remote_contains"] = [item.strip() for item in contains_raw.splitlines() if item.strip()]

    diff_args = ["diff", "--stat", f"{args.good_commit}..{args.compare_ref}"]
    if pathspec:
        diff_args.append("--")
        diff_args.extend(pathspec)
    diffstat = run_git(repo, *diff_args)

    current_branch = run_git(repo, "branch", "--show-current").strip()
    compare_commit = run_git(repo, "rev-parse", args.compare_ref).strip()
    status = run_git(repo, "status", "--short", "--branch")
    github = {
        "prs": collect_pr_evidence(repo, [str(item) for item in args.gh_pr]),
        "runs": collect_run_evidence(repo, [str(item) for item in args.gh_run]),
    }

    payload = {
        "repo": str(repo),
        "good_commit": args.good_commit,
        "compare_ref": args.compare_ref,
        "compare_commit": compare_commit,
        "current_branch": current_branch,
        "focus_paths": pathspec,
        "post_anchor_commits": commit_blocks,
        "diffstat": diffstat.splitlines(),
        "status": status.splitlines(),
        "github": github,
    }

    encoded = json.dumps(payload, indent=2)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded + "\n", encoding="utf-8")
    else:
        sys.stdout.write(encoded + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
