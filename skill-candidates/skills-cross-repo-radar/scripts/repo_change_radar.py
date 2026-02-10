#!/usr/bin/env python3
"""Scan recent multi-repo commit activity and map signals to skill actions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mx3": (
        "mx3",
        "memryx",
        "dfp",
        "mxa",
        "acclbench",
        "accelerator",
        "comfyui",
    ),
    "mcp_bridge": (
        "shim",
        "mcp",
        "bridge",
        "control center",
        "thin-waist",
        "agent",
        "routing",
    ),
    "hardware": (
        "hardware",
        "driver",
        "probe",
        "doctor",
        "firmware",
        "pcie",
        "runtime",
    ),
    "contracts": (
        "contract",
        "schema",
        "fail-closed",
        "policy",
        "boundary",
        "telemetry",
        "validation",
    ),
}


@dataclass
class CommitRecord:
    sha: str
    date: str
    subject: str


@dataclass
class RepoReport:
    repo: str
    path: str
    commits_scanned: int
    hits: dict[str, int]
    sampled_matching_commits: list[str]
    recommended_actions: list[str]
    error: str = ""


@dataclass
class RadarReport:
    since_days: int
    max_commits: int
    repos_scanned: int
    active_repos: int
    reports: list[RepoReport]
    portfolio_actions: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-repo MX3/shim change radar")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Repo spec in the form name=/path/to/repo or /path/to/repo (repeatable)",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=14,
        help="Lookback window in days",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=160,
        help="Maximum commits to scan per repo",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path for JSON report output",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Console output format",
    )
    return parser.parse_args()


def parse_repo_spec(raw: str) -> tuple[str, Path]:
    text = raw.strip()
    if not text:
        raise ValueError("empty --repo value")
    if "=" in text:
        name, path_text = text.split("=", 1)
        repo_name = name.strip()
        repo_path = Path(path_text.strip()).expanduser()
    else:
        repo_path = Path(text).expanduser()
        repo_name = repo_path.name

    if not repo_name:
        raise ValueError(f"invalid repo name in --repo value: {raw!r}")
    return repo_name, repo_path


def collect_commits(repo_path: Path, since_days: int, max_commits: int) -> tuple[list[CommitRecord], str]:
    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        "--since",
        f"{since_days} days ago",
        "--no-merges",
        "--date=short",
        "--pretty=format:%H%x09%ad%x09%s",
        "-n",
        str(max_commits),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip() or "git log failed"
        return [], error

    commits: list[CommitRecord] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, date, subject = parts
        commits.append(CommitRecord(sha=sha, date=date, subject=subject))
    return commits, ""


def score_commits(commits: list[CommitRecord]) -> tuple[dict[str, int], list[str]]:
    hits = {category: 0 for category in CATEGORY_KEYWORDS}
    sample: list[str] = []

    for commit in commits:
        subject_lower = commit.subject.lower()
        matched = False
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in subject_lower for keyword in keywords):
                hits[category] += 1
                matched = True
        if matched and len(sample) < 8:
            sample.append(f"{commit.date} {commit.subject}")

    return hits, sample


def recommend_actions(hits: dict[str, int], commits_scanned: int) -> list[str]:
    actions: list[str] = []
    total_hits = sum(hits.values())

    if commits_scanned == 0:
        return ["No commits in the selected window."]
    if total_hits == 0:
        return ["No MX3/shim drift signals detected; keep current skill set."]

    if hits["mx3"] > 0 or hits["mcp_bridge"] > 0:
        actions.append(
            "Review `repo-b-mcp-comfy-bridge` and `repo-b-local-bridge-orchestrator` for trigger/runbook updates."
        )
    if hits["hardware"] > 0:
        actions.append("Review `repo-b-hardware-first` strict real-hardware commands and diagnostics.")
    if hits["contracts"] > 0:
        actions.append("Review `repo-c-shim-contract-checks` fail-closed contract assumptions.")
    if total_hits >= 6:
        actions.append("Run `$skills-discovery-curation` to triage upgrade and new-skill opportunities.")
        actions.append("Run `$skills-consolidation-architect` if overlap is increasing.")

    return actions


def portfolio_actions(reports: list[RepoReport]) -> tuple[int, list[str]]:
    active = [report for report in reports if not report.error and sum(report.hits.values()) > 0]
    actions: list[str] = []

    if len(active) >= 2:
        actions.append("Enable weekly `skills-cross-repo-radar` scans across active repos.")
        actions.append("Prioritize shared cross-repo skill upgrades before repo-specific one-off skills.")
    elif len(active) == 1:
        actions.append("Keep biweekly radar scans for the single active repo lane.")
    else:
        actions.append("Run monthly radar scans; no active MX3/shim drift signals detected.")

    return len(active), actions


def render_table(report: RadarReport) -> str:
    lines = [
        f"since_days={report.since_days}",
        f"max_commits={report.max_commits}",
        f"repos_scanned={report.repos_scanned}",
        f"active_repos={report.active_repos}",
    ]
    for entry in report.reports:
        lines.append("")
        lines.append(f"[{entry.repo}] path={entry.path}")
        if entry.error:
            lines.append(f"error={entry.error}")
            continue
        lines.append(f"commits_scanned={entry.commits_scanned}")
        lines.append(
            "hits="
            + ",".join(
                f"{category}:{entry.hits.get(category, 0)}"
                for category in ("mx3", "mcp_bridge", "hardware", "contracts")
            )
        )
        if entry.sampled_matching_commits:
            lines.append("sampled_matching_commits:")
            for item in entry.sampled_matching_commits:
                lines.append(f"- {item}")
        lines.append("recommended_actions:")
        for action in entry.recommended_actions:
            lines.append(f"- {action}")

    lines.append("")
    lines.append("portfolio_actions:")
    for action in report.portfolio_actions:
        lines.append(f"- {action}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if not args.repo:
        print("error: at least one --repo value is required", file=sys.stderr)
        return 2
    if args.since_days < 1:
        print("error: --since-days must be >= 1", file=sys.stderr)
        return 2
    if args.max_commits < 1:
        print("error: --max-commits must be >= 1", file=sys.stderr)
        return 2

    reports: list[RepoReport] = []
    for raw_spec in args.repo:
        try:
            repo_name, repo_path = parse_repo_spec(raw_spec)
        except ValueError as exc:
            reports.append(
                RepoReport(
                    repo=f"invalid:{raw_spec}",
                    path="",
                    commits_scanned=0,
                    hits={category: 0 for category in CATEGORY_KEYWORDS},
                    sampled_matching_commits=[],
                    recommended_actions=[],
                    error=str(exc),
                )
            )
            continue

        commits, error = collect_commits(repo_path, args.since_days, args.max_commits)
        if error:
            reports.append(
                RepoReport(
                    repo=repo_name,
                    path=str(repo_path),
                    commits_scanned=0,
                    hits={category: 0 for category in CATEGORY_KEYWORDS},
                    sampled_matching_commits=[],
                    recommended_actions=[],
                    error=error,
                )
            )
            continue

        hits, sample = score_commits(commits)
        reports.append(
            RepoReport(
                repo=repo_name,
                path=str(repo_path),
                commits_scanned=len(commits),
                hits=hits,
                sampled_matching_commits=sample,
                recommended_actions=recommend_actions(hits, len(commits)),
            )
        )

    active_repos, actions = portfolio_actions(reports)
    report = RadarReport(
        since_days=args.since_days,
        max_commits=args.max_commits,
        repos_scanned=len(reports),
        active_repos=active_repos,
        reports=reports,
        portfolio_actions=actions,
    )

    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(render_table(report))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
