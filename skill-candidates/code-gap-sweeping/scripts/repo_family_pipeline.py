#!/usr/bin/env python3
"""Build a deterministic cross-repo pipeline command matrix."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import sys
from typing import Any

REPO_PAIR_RE = re.compile(r"^([^=]+)=(.+)$")

ALLOWED_FAMILIES = {"repo_a", "repo_b", "repo_c", "repo_d", "generic"}

FAMILY_SKILLS: dict[str, list[str]] = {
    "repo_a": [
        "repo-a-policy-selftest-gate",
        "repo-a-coordinator-smoke",
        "repo-a-telemetry-kv-guard",
    ],
    "repo_b": [
        "repo-b-local-bridge-orchestrator",
        "repo-b-mcp-comfy-bridge",
        "repo-b-comfy-amuse-capcut-pipeline",
        "repo-b-thin-waist-routing",
        "repo-b-preflight-doc-sync",
        "repo-b-hardware-first",
    ],
    "repo_c": [
        "repo-c-boundary-governance",
        "repo-c-policy-schema-gate",
        "repo-c-ranking-contracts",
        "repo-c-shim-contract-checks",
        "repo-c-trace-ndjson-validate",
        "repo-c-persona-registry-maintenance",
    ],
    "repo_d": [
        "repo-d-ui-guardrails",
        "repo-d-setup-diagnostics",
        "repo-d-local-packaging",
    ],
    "generic": [],
}

COMMON_SKILLS = [
    "skill-hub",
    "skill-common-sense-engineering",
    "code-gap-sweeping",
    "request-loopback-resume",
    "skill-installer-plus",
    "skill-auditor",
    "skill-enforcer",
    "skill-arbiter-lockdown-admission",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate all-repo pipeline command matrix")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help='Repo mapping as "name=/path/to/repo" (repeatable)',
    )
    parser.add_argument(
        "--repos-root",
        action="append",
        default=[],
        help="Directory containing git repos as immediate child folders (repeatable)",
    )
    parser.add_argument(
        "--exclude-repo",
        action="append",
        default=[],
        help="Repo name to skip after discovery (repeatable)",
    )
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help='Family assignment as "name=repo_a|repo_b|repo_c|repo_d|generic" (repeatable)',
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=14,
        help="Gap sweep patch window",
    )
    parser.add_argument("--base-ref", default="main", help="Preferred base ref")
    parser.add_argument(
        "--state-dir",
        default="/tmp/workstream-states",
        help="Directory for request-loopback-resume state files",
    )
    parser.add_argument(
        "--evidence-dir",
        default="/tmp",
        help="Directory for JSON evidence outputs",
    )
    parser.add_argument(
        "--installer-ledger",
        default='"$CODEX_HOME/skills/.skill-installer-plus-ledger.json"',
        help="Path or shell expression for installer ledger in generated commands",
    )
    parser.add_argument(
        "--installer-dest",
        default='"$CODEX_HOME/skills"',
        help="Path or shell expression for installer destination in generated commands",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--bash-out", default="", help="Optional bash script output path")
    return parser.parse_args()


def parse_repo_pair(raw: str) -> tuple[str, Path]:
    match = REPO_PAIR_RE.match(str(raw or "").strip())
    if not match:
        raise ValueError(f"invalid --repo value: {raw!r}; expected name=/path/to/repo")
    name = match.group(1).strip()
    path = Path(match.group(2).strip()).expanduser().resolve()
    if not name:
        raise ValueError("repo name cannot be empty")
    if not path.is_dir():
        raise ValueError(f"repo path not found: {path}")
    if not (path / ".git").exists():
        raise ValueError(f"not a git repository: {path}")
    return name, path


def parse_family_pair(raw: str) -> tuple[str, str]:
    match = REPO_PAIR_RE.match(str(raw or "").strip())
    if not match:
        raise ValueError(f"invalid --family value: {raw!r}; expected name=family")
    name = match.group(1).strip()
    family = match.group(2).strip().lower()
    if family not in ALLOWED_FAMILIES:
        allowed = ", ".join(sorted(ALLOWED_FAMILIES))
        raise ValueError(f"invalid family {family!r}; expected one of: {allowed}")
    return name, family


def discover_repos_under_root(root: Path) -> list[tuple[str, Path]]:
    if not root.is_dir():
        raise ValueError(f"--repos-root not found: {root}")
    repos: list[tuple[str, Path]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            repos.append((child.name, child.resolve()))
    return repos


def infer_family(repo_name: str) -> str:
    key = repo_name.strip().lower()
    if "repo-a" in key or "private_repo_a" in key:
        return "repo_a"
    if "repo-b" in key or "private_repo_b" in key:
        return "repo_b"
    if "repo-c" in key or "private_repo_c" in key:
        return "repo_c"
    if "repo-d" in key or "private_repo_d" in key:
        return "repo_d"
    return "generic"


def slugify(repo_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", repo_name.lower()).strip("-")
    return slug or "repo"


def cmd_join(parts: list[str]) -> str:
    return " ".join(parts)


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_bash(path_text: str, commands: list[str]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated by repo_family_pipeline.py",
        *commands,
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def build_repo_commands(
    repo_name: str,
    repo_path: Path,
    family: str,
    since_days: int,
    base_ref: str,
    state_dir: str,
    evidence_dir: str,
) -> dict[str, str]:
    slug = slugify(repo_name)
    lane = f"{family} implementation lane"
    state_file = f"{state_dir.rstrip('/')}/{slug}.json"
    gap_report = f"{evidence_dir.rstrip('/')}/{slug}-code-gap.json"
    resume_report = f"{evidence_dir.rstrip('/')}/{slug}-resume.json"

    repo_pair = f"{repo_name}={repo_path}"

    init_cmd = cmd_join(
        [
            "python3",
            "skill-candidates/request-loopback-resume/scripts/workstream_resume.py",
            "init",
            "--state-file",
            shlex.quote(state_file),
            "--task",
            shlex.quote(f"Cross-repo pipeline: {repo_name}"),
            "--lane",
            shlex.quote("gap sweep"),
            "--lane",
            shlex.quote(lane),
            "--lane",
            shlex.quote("docs+release"),
            "--in-progress",
            shlex.quote("gap sweep"),
        ]
    )

    gap_cmd = cmd_join(
        [
            "python3",
            "skill-candidates/code-gap-sweeping/scripts/code_gap_sweep.py",
            "--repo",
            shlex.quote(repo_pair),
            "--since-days",
            str(since_days),
            "--base-ref",
            shlex.quote(base_ref),
            "--json-out",
            shlex.quote(gap_report),
        ]
    )

    set_cmd = cmd_join(
        [
            "python3",
            "skill-candidates/request-loopback-resume/scripts/workstream_resume.py",
            "set",
            "--state-file",
            shlex.quote(state_file),
            "--lane-status",
            shlex.quote("gap sweep=completed"),
            "--lane-status",
            shlex.quote(f"{lane}=in_progress"),
            "--lane-next",
            shlex.quote(f"{lane}=Run {family} skill pack checks"),
            "--artifact",
            shlex.quote(gap_report),
            "--note",
            shlex.quote("pipeline handoff after gap sweep"),
        ]
    )

    validate_cmd = cmd_join(
        [
            "python3",
            "skill-candidates/request-loopback-resume/scripts/workstream_resume.py",
            "validate",
            "--state-file",
            shlex.quote(state_file),
        ]
    )

    resume_cmd = cmd_join(
        [
            "python3",
            "skill-candidates/request-loopback-resume/scripts/workstream_resume.py",
            "resume",
            "--state-file",
            shlex.quote(state_file),
            "--json-out",
            shlex.quote(resume_report),
        ]
    )

    return {
        "state_file": state_file,
        "gap_report": gap_report,
        "resume_report": resume_report,
        "init": init_cmd,
        "gap_sweep": gap_cmd,
        "checkpoint": set_cmd,
        "validate": validate_cmd,
        "resume": resume_cmd,
    }


def build_family_admission_commands(
    family: str,
    skills: list[str],
    evidence_dir: str,
    installer_ledger: str,
    installer_dest: str,
) -> dict[str, Any]:
    if not skills:
        return {
            "family": family,
            "skills": [],
            "arbiter_command": "",
            "installer_plan_command": "",
            "installer_admit_commands": [],
        }

    evidence_root = evidence_dir.rstrip("/")
    family_slug = family.replace("_", "-")
    arbiter_json = f"{evidence_root}/{family_slug}-skill-pack-arbiter.json"

    arbiter_command = cmd_join(
        [
            "python3",
            "scripts/arbitrate_skills.py",
            *[shlex.quote(skill) for skill in skills],
            "--source-dir",
            "skill-candidates",
            "--window",
            "10",
            "--baseline-window",
            "3",
            "--threshold",
            "3",
            "--max-rg",
            "3",
            "--personal-lockdown",
            "--json-out",
            shlex.quote(arbiter_json),
        ]
    )

    installer_plan_json = f"{evidence_root}/{family_slug}-installer-plan.json"
    installer_plan_command = cmd_join(
        [
            "python3",
            "skill-candidates/skill-installer-plus/scripts/skill_installer_plus.py",
            "--ledger",
            installer_ledger,
            "plan",
            "--skills-root",
            "skill-candidates",
            "--dest",
            installer_dest,
            "--json-out",
            shlex.quote(installer_plan_json),
        ]
    )

    installer_admit_commands: list[str] = []
    for skill in skills:
        admit_json = f"{evidence_root}/{family_slug}-{skill}-installer-admit.json"
        admit_arbiter_json = f"{evidence_root}/{family_slug}-{skill}-installer-arbiter.json"
        command = cmd_join(
            [
                "python3",
                "skill-candidates/skill-installer-plus/scripts/skill_installer_plus.py",
                "--ledger",
                installer_ledger,
                "admit",
                "--skill",
                shlex.quote(skill),
                "--source-dir",
                "skill-candidates",
                "--dest",
                installer_dest,
                "--window",
                "10",
                "--baseline-window",
                "3",
                "--threshold",
                "3",
                "--max-rg",
                "3",
                "--arbiter-json",
                shlex.quote(admit_arbiter_json),
                "--json-out",
                shlex.quote(admit_json),
            ]
        )
        installer_admit_commands.append(command)

    return {
        "family": family,
        "skills": skills,
        "arbiter_command": arbiter_command,
        "installer_plan_command": installer_plan_command,
        "installer_admit_commands": installer_admit_commands,
    }


def main() -> int:
    args = parse_args()

    repos: list[tuple[str, Path]] = []
    seen_names: set[str] = set()

    for raw in args.repo:
        try:
            name, path = parse_repo_pair(raw)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if name in seen_names:
            print(f"error: duplicate repo name: {name}", file=sys.stderr)
            return 2
        seen_names.add(name)
        repos.append((name, path))

    for raw_root in args.repos_root:
        root = Path(str(raw_root).strip()).expanduser().resolve()
        try:
            discovered = discover_repos_under_root(root)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for name, path in discovered:
            if name in seen_names:
                continue
            seen_names.add(name)
            repos.append((name, path))

    excludes = {str(item or "").strip() for item in args.exclude_repo if str(item or "").strip()}
    if excludes:
        repos = [(name, path) for name, path in repos if name not in excludes]

    if not repos:
        print(
            "error: no repositories selected; provide --repo and/or --repos-root",
            file=sys.stderr,
        )
        return 2

    family_overrides: dict[str, str] = {}
    for raw in args.family:
        try:
            name, family = parse_family_pair(raw)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        family_overrides[name] = family

    repo_rows: list[dict[str, Any]] = []
    family_present: dict[str, list[str]] = {}

    for repo_name, repo_path in repos:
        family = family_overrides.get(repo_name) or infer_family(repo_name)
        if family not in ALLOWED_FAMILIES:
            family = "generic"
        family_present.setdefault(family, []).append(repo_name)

        commands = build_repo_commands(
            repo_name=repo_name,
            repo_path=repo_path,
            family=family,
            since_days=args.since_days,
            base_ref=args.base_ref,
            state_dir=args.state_dir,
            evidence_dir=args.evidence_dir,
        )

        repo_rows.append(
            {
                "repo": repo_name,
                "path": str(repo_path),
                "family": family,
                "common_skills": list(COMMON_SKILLS),
                "family_skill_pack": list(FAMILY_SKILLS.get(family, [])),
                "commands": commands,
            }
        )

    all_repos_gap_parts = [
        "python3",
        "skill-candidates/code-gap-sweeping/scripts/code_gap_sweep.py",
    ]
    for repo_name, repo_path in repos:
        all_repos_gap_parts.extend(["--repo", shlex.quote(f"{repo_name}={repo_path}")])
    all_repos_gap_parts.extend(
        [
            "--since-days",
            str(args.since_days),
            "--base-ref",
            shlex.quote(args.base_ref),
            "--json-out",
            shlex.quote(f"{args.evidence_dir.rstrip('/')}/all-repos-code-gap.json"),
        ]
    )
    all_repos_gap_command = cmd_join(all_repos_gap_parts)

    family_packs: list[dict[str, Any]] = []
    for family in sorted(family_present.keys()):
        skills = list(FAMILY_SKILLS.get(family, []))
        family_packs.append(
            build_family_admission_commands(
                family=family,
                skills=skills,
                evidence_dir=args.evidence_dir,
                installer_ledger=args.installer_ledger,
                installer_dest=args.installer_dest,
            )
        )

    payload: dict[str, Any] = {
        "generated_at": now_iso(),
        "since_days": args.since_days,
        "base_ref": args.base_ref,
        "repos": repo_rows,
        "family_packs": family_packs,
        "global_commands": {
            "all_repos_gap_sweep": all_repos_gap_command,
            "skill_game_template": (
                "python3 scripts/skill_game.py --task 'cross-repo pipeline run' "
                "--used-skill skill-hub --used-skill skill-common-sense-engineering "
                "--used-skill code-gap-sweeping --used-skill request-loopback-resume "
                "--used-skill skill-installer-plus --used-skill skill-auditor "
                "--used-skill skill-enforcer --used-skill skill-arbiter-lockdown-admission "
                "--arbiter-report /tmp/all-repo-skill-pack-arbiter.json "
                "--audit-report /tmp/all-repo-audit.json --enforcer-pass"
            ),
        },
    }

    write_json(args.json_out, payload)

    bash_commands: list[str] = []
    bash_commands.append("# Global gap sweep")
    bash_commands.append(all_repos_gap_command)
    for row in repo_rows:
        repo = row["repo"]
        cmds = row["commands"]
        bash_commands.append("")
        bash_commands.append(f"# Pipeline checkpoint lane for {repo}")
        bash_commands.append(cmds["init"])
        bash_commands.append(cmds["gap_sweep"])
        bash_commands.append(cmds["checkpoint"])
        bash_commands.append(cmds["validate"])
        bash_commands.append(cmds["resume"])

    for pack in family_packs:
        if not pack.get("skills"):
            continue
        bash_commands.append("")
        bash_commands.append(f"# Family admission lane: {pack['family']}")
        bash_commands.append(pack["arbiter_command"])
        bash_commands.append(pack["installer_plan_command"])
        for command in pack["installer_admit_commands"]:
            bash_commands.append(command)

    write_bash(args.bash_out, bash_commands)

    print("repo,family,pack_skills,state_file,gap_report")
    for row in repo_rows:
        repo = row["repo"]
        family = row["family"]
        skills = row["family_skill_pack"]
        state_file = row["commands"]["state_file"]
        gap_report = row["commands"]["gap_report"]
        print(f"{repo},{family},{len(skills)},{state_file},{gap_report}")

    print("families=" + ",".join(sorted(family_present.keys())))
    if args.json_out:
        print(f"json_out={args.json_out}")
    if args.bash_out:
        print(f"bash_out={args.bash_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
