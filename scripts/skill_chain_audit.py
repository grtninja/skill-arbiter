#!/usr/bin/env python3
"""Audit activated skills and build deterministic chaining workflows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Callable


INTERNAL_DIR_NAMES = {".system", "_blacklisted-archive", "_nested-dedupe-archive"}


@dataclass(frozen=True)
class SkillInfo:
    name: str
    path: Path
    source: str  # top-level or system
    description: str


@dataclass(frozen=True)
class ChainSpec:
    chain_id: str
    title: str
    vendor: str
    intent: str
    matcher: Callable[[SkillInfo], bool]
    extra_steps: tuple[str, ...] = ()
    multi_repo: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build full skill-chain coverage workflows")
    parser.add_argument(
        "--skills-root",
        default=str(Path.home() / ".codex" / "skills"),
        help="Activated skills root",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional JSON output path",
    )
    parser.add_argument(
        "--md-out",
        default="",
        help="Optional Markdown output path",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include skills from .system directory",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Console output format",
    )
    return parser.parse_args()


def parse_frontmatter_description(text: str) -> str:
    match = re.match(r"(?s)^---\n(.*?)\n---\n?", text)
    if not match:
        return ""
    block = match.group(1)
    for line in block.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def read_description(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ""
    raw = skill_md.read_text(encoding="utf-8", errors="ignore")
    return parse_frontmatter_description(raw)


def collect_skills(skills_root: Path, include_system: bool) -> list[SkillInfo]:
    skills: list[SkillInfo] = []
    for entry in sorted(skills_root.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name.startswith("_") or entry.name in INTERNAL_DIR_NAMES:
            continue
        skills.append(
            SkillInfo(
                name=entry.name,
                path=entry,
                source="top-level",
                description=read_description(entry),
            )
        )

    system_root = skills_root / ".system"
    if include_system and system_root.is_dir():
        for entry in sorted(system_root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir():
                continue
            skills.append(
                SkillInfo(
                    name=entry.name,
                    path=entry,
                    source="system",
                    description=read_description(entry),
                )
            )
    return skills


def build_chain_specs() -> list[ChainSpec]:
    def in_set(names: set[str]) -> Callable[[SkillInfo], bool]:
        return lambda skill: skill.name in names

    return [
        ChainSpec(
            chain_id="governance-core",
            title="Governance Core Chain",
            vendor="internal",
            intent="Route, budget, audit, admission, and policy alignment for all skill-driven work.",
            matcher=lambda skill: skill.name.startswith("skill-")
            or skill.name.startswith("skills-")
            or skill.name
            in {
                "multitask-orchestrator",
                "usage-watcher",
                "code-gap-sweeping",
                "docs-alignment-lock",
                "request-loopback-resume",
                "safe-mass-index-core",
                "local-compute-usage",
                "playwright-safe",
                "playwright-edge-preference",
            },
            extra_steps=("docs-alignment-lock",),
            multi_repo=True,
        ),
        ChainSpec(
            chain_id="repo-a-ddc",
            title="Repo A DDC Chain",
            vendor="<PRIVATE_REPO_A>",
            intent="Coordinator smoke, policy self-test, and telemetry/KV guard execution for Repo A lanes.",
            matcher=lambda skill: skill.name.startswith("repo-a-"),
            multi_repo=True,
        ),
        ChainSpec(
            chain_id="repo-b-ops",
            title="Repo B Operations Chain",
            vendor="<PRIVATE_REPO_B>",
            intent="Control center, bridge, routing, and Comfy orchestration workflows for Repo B.",
            matcher=lambda skill: skill.name.startswith("repo-b-"),
            multi_repo=True,
        ),
        ChainSpec(
            chain_id="repo-c-governance",
            title="Repo C Governance Chain",
            vendor="<PRIVATE_REPO_C>",
            intent="Policy schema, ranking contracts, trace validation, and persona registry maintenance.",
            matcher=lambda skill: skill.name.startswith("repo-c-"),
            multi_repo=True,
        ),
        ChainSpec(
            chain_id="repo-d-packaging",
            title="Repo D UI Packaging Chain",
            vendor="<PRIVATE_REPO_D>",
            intent="Desktop setup, UI guardrails, mass index, and local packaging validation for Repo D.",
            matcher=lambda skill: skill.name.startswith("repo-d-"),
            multi_repo=True,
        ),
        ChainSpec(
            chain_id="web-deploy-vendors",
            title="Web Deployment Vendor Chain",
            vendor="Cloudflare/Netlify/Render/Vercel",
            intent="Deploy web projects with vendor-specific CLI pathways and deterministic release checks.",
            matcher=in_set({"cloudflare-deploy", "netlify-deploy", "render-deploy", "vercel-deploy"}),
            extra_steps=("skill-arbiter-release-ops",),
        ),
        ChainSpec(
            chain_id="github-devops",
            title="GitHub DevOps Chain",
            vendor="GitHub",
            intent="Issue/PR triage, CI remediation, and comment resolution using GitHub tooling.",
            matcher=in_set({"github", "gh-issues", "gh-address-comments", "gh-fix-ci", "coding-agent", "diffs"}),
            extra_steps=("session-logs", "healthcheck"),
        ),
        ChainSpec(
            chain_id="notion-linear-pm",
            title="Notion + Linear PM Chain",
            vendor="Notion/Linear",
            intent="Planning, knowledge capture, and issue workflow orchestration.",
            matcher=lambda skill: skill.name.startswith("notion") or skill.name == "linear",
            extra_steps=("docs-alignment-lock",),
        ),
        ChainSpec(
            chain_id="openai-media-ai",
            title="OpenAI Media AI Chain",
            vendor="OpenAI",
            intent="Image, audio, video, speech, and transcript generation workflows.",
            matcher=in_set(
                {
                    "imagegen",
                    "openai-image-gen",
                    "openai-whisper",
                    "openai-whisper-api",
                    "sora",
                    "speech",
                    "transcribe",
                    "video-frames",
                    "nano-banana-pro",
                    "songsee",
                    "sherpa-onnx-tts",
                    "model-usage",
                }
            ),
            extra_steps=("openai-docs",),
        ),
        ChainSpec(
            chain_id="browser-design-automation",
            title="Browser + Design Automation Chain",
            vendor="Playwright/Figma",
            intent="Cross-browser automation, screenshot evidence, and design-to-code implementation.",
            matcher=in_set(
                {
                    "playwright",
                    "playwright-safe",
                    "playwright-edge-preference",
                    "figma",
                    "figma-implement-design",
                    "screenshot",
                    "develop-web-game",
                }
            ),
            extra_steps=("code-gap-sweeping",),
        ),
        ChainSpec(
            chain_id="docs-data-assets",
            title="Docs + Data Asset Chain",
            vendor="Productivity",
            intent="Structured document, PDF, spreadsheet, and notebook workflows.",
            matcher=in_set({"doc", "pdf", "spreadsheet", "jupyter-notebook"}),
        ),
        ChainSpec(
            chain_id="security-assurance",
            title="Security Assurance Chain",
            vendor="Security",
            intent="Security best-practice review, threat modeling, and ownership-risk mapping.",
            matcher=lambda skill: skill.name.startswith("security-") or skill.name == "sentry",
            extra_steps=("skill-enforcer",),
        ),
        ChainSpec(
            chain_id="apple-mac-productivity",
            title="Apple/Mac Productivity Chain",
            vendor="Apple/macOS",
            intent="Notes, reminders, tasks, and local messaging/productivity automation on macOS.",
            matcher=in_set(
                {
                    "apple-notes",
                    "apple-reminders",
                    "bear-notes",
                    "things-mac",
                    "imsg",
                    "bluebubbles",
                    "obsidian",
                    "notion",
                    "trello",
                }
            ),
        ),
        ChainSpec(
            chain_id="collab-communication",
            title="Collaboration Communication Chain",
            vendor="Slack/Discord/Feishu",
            intent="Team communication and collaborative docs/drive permission workflows.",
            matcher=lambda skill: skill.name in {"slack", "discord"}
            or skill.name.startswith("feishu-"),
            extra_steps=("docs-alignment-lock",),
        ),
        ChainSpec(
            chain_id="openclaw-acp-vendor",
            title="OpenClaw ACP Vendor Chain",
            vendor="OpenClaw/ACP",
            intent="Vendor-specific ACP routing, utility toolchains, and command-lane orchestration.",
            matcher=in_set(
                {
                    "acp-router",
                    "clawhub",
                    "gemini",
                    "gog",
                    "goplaces",
                    "eightctl",
                    "ordercli",
                    "peekaboo",
                    "mcporter",
                    "blogwatcher",
                    "sag",
                    "gifgrep",
                    "healthcheck",
                    "himalaya",
                    "nano-pdf",
                    "oracle",
                    "prose",
                    "lobster",
                    "canvas",
                    "tmux",
                    "1password",
                    "voice-call",
                    "wacli",
                    "weather",
                    "sonoscli",
                    "spotify-player",
                    "openhue",
                    "summarize",
                    "xurl",
                    "blucli",
                    "camsnap",
                    "session-logs",
                }
            ),
        ),
        ChainSpec(
            chain_id="microsoft-native-apps",
            title="Microsoft Native App Chain",
            vendor="Microsoft/.NET",
            intent="Native .NET and desktop app build scaffolding/workflow chaining.",
            matcher=in_set({"aspnet-core", "winui-app"}),
            extra_steps=("code-gap-sweeping",),
        ),
        ChainSpec(
            chain_id="vrm-avatar-pipeline",
            title="VRM Avatar Pipeline Chain",
            vendor="Blender/VRM",
            intent="Template normalization, visible fit, animation export, and roundtrip quality gates.",
            matcher=lambda skill: skill.name.startswith("vrm-")
            or skill.name.startswith("vroid-")
            or skill.name.startswith("blender-vrm-"),
        ),
        ChainSpec(
            chain_id="utility-general",
            title="General Utility Chain",
            vendor="Mixed",
            intent="Catch-all fallback for utility skills without a strong vendor lane.",
            matcher=in_set({"chatgpt-apps", "openai-docs", "yeet", "skill-creator", "skill-installer"}),
        ),
    ]


def unique_steps(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        out.append(item)
        seen.add(item)
    return out


def build_base_steps(multitask_present: bool) -> list[str]:
    steps = [
        "skill-hub",
        "multitask-orchestrator" if multitask_present else "manual-lane-split-fallback",
        "skill-common-sense-engineering",
        "usage-watcher",
        "skill-cost-credit-governor",
        "skill-cold-start-warm-path-optimizer",
    ]
    return steps


def add_multi_repo_steps(steps: list[str]) -> list[str]:
    return steps + ["skills-cross-repo-radar", "code-gap-sweeping", "request-loopback-resume"]


def add_governance_tail(steps: list[str]) -> list[str]:
    return steps + ["skill-installer-plus", "skill-auditor", "skill-arbiter-lockdown-admission", "skill-enforcer"]


def chain_for_spec(
    spec: ChainSpec,
    matched_skills: list[SkillInfo],
    multitask_present: bool,
) -> dict[str, object]:
    base = build_base_steps(multitask_present)
    if spec.multi_repo:
        base = add_multi_repo_steps(base)
    steps = add_governance_tail(base + list(spec.extra_steps) + [skill.name for skill in matched_skills])
    steps = unique_steps(steps)
    return {
        "chain_id": spec.chain_id,
        "title": spec.title,
        "vendor": spec.vendor,
        "intent": spec.intent,
        "steps": steps,
        "skills_covered": [skill.name for skill in matched_skills],
        "skills_covered_count": len(matched_skills),
    }


def build_report(skills: list[SkillInfo], multitask_present: bool) -> dict[str, object]:
    specs = build_chain_specs()
    chain_rows: list[dict[str, object]] = []
    skill_to_chains: dict[str, list[str]] = {skill.name: [] for skill in skills}

    for spec in specs:
        matched = [skill for skill in skills if spec.matcher(skill)]
        if not matched:
            continue
        row = chain_for_spec(spec, matched, multitask_present)
        chain_rows.append(row)
        for skill in matched:
            skill_to_chains[skill.name].append(spec.chain_id)

    uncovered = sorted([name for name, chains in skill_to_chains.items() if not chains])
    if uncovered:
        fallback_skills = [skill for skill in skills if skill.name in uncovered]
        fallback = chain_for_spec(
            ChainSpec(
                chain_id="coverage-fallback",
                title="Coverage Fallback Chain",
                vendor="Mixed",
                intent="Guarantee chain coverage for remaining activated skills.",
                matcher=lambda _: False,
            ),
            fallback_skills,
            multitask_present,
        )
        chain_rows.append(fallback)
        for skill in fallback_skills:
            skill_to_chains[skill.name].append("coverage-fallback")
        uncovered = []

    per_skill: list[dict[str, object]] = []
    for skill in sorted(skills, key=lambda s: s.name.lower()):
        per_skill.append(
            {
                "skill": skill.name,
                "source": skill.source,
                "description": skill.description,
                "chains": sorted(skill_to_chains.get(skill.name, [])),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "activated_skill_count": len(skills),
            "chain_count": len(chain_rows),
            "multitask_skill_present": multitask_present,
            "multitask_step": "multitask-orchestrator" if multitask_present else "manual-lane-split-fallback",
            "uncovered_skill_count": len(uncovered),
        },
        "base_control_chain": add_governance_tail(build_base_steps(multitask_present)),
        "chain_workflows": sorted(chain_rows, key=lambda row: str(row["chain_id"])),
        "skills": per_skill,
        "uncovered_skills": uncovered,
    }


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    chains = report["chain_workflows"]
    skills = report["skills"]
    base_chain = report["base_control_chain"]

    lines: list[str] = []
    lines.append("# Complete Activated Skill Chain Workflow Audit")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Activated skills audited: `{summary['activated_skill_count']}`")
    lines.append(f"- Workflow chains generated: `{summary['chain_count']}`")
    lines.append(f"- Multitasking skill present: `{summary['multitask_skill_present']}`")
    lines.append(f"- Multitasking step used: `{summary['multitask_step']}`")
    lines.append(f"- Uncovered skills: `{summary['uncovered_skill_count']}`")
    lines.append("")
    lines.append("## Base Control Chain")
    lines.append("")
    for idx, step in enumerate(base_chain, start=1):
        lines.append(f"{idx}. `{step}`")
    lines.append("")
    lines.append("## Chain Workflows")
    lines.append("")
    for chain in chains:
        lines.append(f"### {chain['title']} (`{chain['chain_id']}`)")
        lines.append("")
        lines.append(f"- Vendor: `{chain['vendor']}`")
        lines.append(f"- Intent: {chain['intent']}")
        lines.append(f"- Skills covered: `{chain['skills_covered_count']}`")
        lines.append("- Steps:")
        for idx, step in enumerate(chain["steps"], start=1):
            lines.append(f"{idx}. `{step}`")
        lines.append("- Covered skills:")
        for skill in chain["skills_covered"]:
            lines.append(f"  - `{skill}`")
        lines.append("")
    lines.append("## Per-Skill Chain Coverage")
    lines.append("")
    lines.append("| Skill | Source | Chains |")
    lines.append("| --- | --- | --- |")
    for row in skills:
        chains_text = ", ".join(f"`{item}`" for item in row["chains"]) if row["chains"] else "`(none)`"
        lines.append(f"| `{row['skill']}` | `{row['source']}` | {chains_text} |")
    lines.append("")
    lines.append("## Multitasking Policy")
    lines.append("")
    if summary["multitask_skill_present"]:
        lines.append("- `multitask-orchestrator` is installed and should be used after `skill-hub` for 2+ independent lanes.")
    else:
        lines.append(
            "- `multitask-orchestrator` is not installed; apply explicit manual lane split/merge after `skill-hub`."
        )
        lines.append("- Manual multitask fallback: define lanes, run each lane with full guardrails, then merge with policy checks.")
    lines.append("")
    return "\n".join(lines)


def print_table(report: dict[str, object]) -> None:
    summary = report["summary"]
    print(f"activated_skills: {summary['activated_skill_count']}")
    print(f"chain_count: {summary['chain_count']}")
    print(f"multitask_skill_present: {summary['multitask_skill_present']}")
    print(f"multitask_step: {summary['multitask_step']}")
    print(f"uncovered_skill_count: {summary['uncovered_skill_count']}")
    print("")
    print("chains:")
    for row in report["chain_workflows"]:
        print(
            f"- {row['chain_id']}: vendor={row['vendor']} skills={row['skills_covered_count']}"
        )


def write_text(path_text: str, content: str) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path_text: str, payload: dict[str, object]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.is_dir():
        raise SystemExit(f"skills root not found: {skills_root}")

    skills = collect_skills(skills_root, include_system=args.include_system)
    installed_names = {skill.name for skill in skills}
    multitask_present = "multitask-orchestrator" in installed_names

    report = build_report(skills, multitask_present=multitask_present)
    markdown = render_markdown(report)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_table(report)

    write_json(args.json_out, report)
    write_text(args.md_out, markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
