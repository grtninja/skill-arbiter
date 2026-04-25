#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path
import subprocess
import sys

if __package__ in {None, ""}:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[0]
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(repo_root))

from generate_vscode_codex_skill_matrix import render_matrix as render_vscode_matrix
from skill_arbiter.inventory import build_inventory_snapshot
from skill_arbiter.paths import REPO_ROOT

PUBLIC_CATALOG_ADVISOR_NOTE = "_Live local advisor note omitted from public-shape catalog._"
FRONTMATTER_RE = re.compile(r"(?s)^---\n(.*?)\n---\n?")


def _md_cell(value: object, *, fallback: str = "-") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text.replace("|", "\\|").replace("\n", " ")


def _read_skill_frontmatter(skill_path: Path) -> dict[str, str]:
    if not skill_path.is_file():
        return {}
    text = skill_path.read_text(encoding="utf-8", errors="ignore")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def _repo_skill_paths(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "SKILL.md", "skill-candidates/*/SKILL.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error_text = str(getattr(result, "stderr", "") or "").strip()
        raise RuntimeError(
            "git ls-files failed while building the public skill catalog; "
            "refusing to scan untracked skills. "
            + (error_text if error_text else "Run the generator from a tracked git worktree.")
        )
    return [repo_root / line.strip() for line in result.stdout.splitlines() if line.strip()]


def _catalog_metadata(metadata: dict[str, str]) -> dict[str, str]:
    author = str(metadata.get("author") or "").strip()
    canonical_source = str(metadata.get("canonical_source") or "").strip()
    if not author or not canonical_source:
        return {
            "description": "",
            "author": "",
            "canonical_source": "",
        }
    return {
        "description": str(metadata.get("description") or "").strip(),
        "author": author,
        "canonical_source": canonical_source,
    }


def collect_repo_skill_index(repo_root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for skill_path in _repo_skill_paths(repo_root):
        metadata = _read_skill_frontmatter(skill_path)
        catalog_metadata = _catalog_metadata(metadata)
        rel_path = skill_path.relative_to(repo_root).as_posix()
        if rel_path == "SKILL.md":
            scope = "repo_root"
            skill_name = str(metadata.get("name") or "skill-arbiter")
        else:
            scope = "skill_candidate"
            skill_name = skill_path.parent.name
        entries.append(
            {
                "name": skill_name,
                "scope": scope,
                "description": catalog_metadata["description"],
                "author": catalog_metadata["author"],
                "canonical_source": catalog_metadata["canonical_source"],
                "path": rel_path,
            }
        )
    return sorted(entries, key=lambda item: (item["scope"], item["name"].lower()))


def render_repo_catalog(*, repo_root: Path, generated_at: str) -> str:
    entries = collect_repo_skill_index(repo_root)
    repo_root_count = sum(1 for item in entries if item["scope"] == "repo_root")
    candidate_count = sum(1 for item in entries if item["scope"] == "skill_candidate")
    lines = [
        "# skill-arbiter Skill Catalog",
        "",
        "This is the canonical repo-owned skill index for `skill-arbiter`.",
        "Use this page as the stable discovery surface for humans, mirrors, and crawlers.",
        "",
        "## Catalog Summary",
        "",
        f"- Generated: `{generated_at}`",
        f"- Total repo skills: `{len(entries)}`",
        f"- Repo-root skills: `{repo_root_count}`",
        f"- Candidate skills: `{candidate_count}`",
        "",
        "## Discovery Notes",
        "",
        "- `skill-catalog.md` is the intentional repo-owned discovery index.",
        "- `references/skill-catalog.md` remains the deeper inventory and governance view.",
        "- Catalog metadata is emitted only when a skill declares explicit `author` and `canonical_source` frontmatter.",
        "- Rows without explicit provenance metadata stay blank instead of inventing attribution or copying noisy descriptions.",
        "",
        "## Repo Skills",
        "",
        "| Skill | Scope | Description | Author | Canonical Source | Path |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in entries:
        lines.append(
            "| `{name}` | `{scope}` | {description} | {author} | {canonical_source} | `{path}` |".format(
                name=_md_cell(row["name"]),
                scope=_md_cell(row["scope"]),
                description=_md_cell(row["description"]),
                author=_md_cell(row["author"]),
                canonical_source=_md_cell(row["canonical_source"]),
                path=row["path"],
            )
        )
    return "\n".join(lines) + "\n"


def render_catalog(payload: dict[str, object]) -> str:
    skills = payload.get("skills", [])
    sources = payload.get("sources", [])
    incidents = payload.get("incidents", [])
    recent_work = payload.get("recent_work_skills", [])
    legitimacy = payload.get("legitimacy_summary", {})
    interop_sources = payload.get("interop_sources", [])
    generated_at = os.environ.get("SKILL_CATALOG_GENERATED_AT") or str(payload.get("generated_at", ""))
    lines = [
        "# NullClaw Skill Catalog",
        "",
        "This document is machine-generated by `scripts/generate_skill_catalog.py` from the live NullClaw inventory model.",
        "",
        "## Inventory Summary",
        "",
        f"- Generated: `{generated_at}`",
        "- Host ID: `<LOCAL_HOST_ID>`",
        f"- Skill records: `{len(skills)}`",
        f"- Source records: `{len(sources)}`",
        f"- Incident records: `{len(incidents)}`",
        f"- Recent-work-relevant skills: `{len(recent_work)}`",
        "",
        "## Legitimacy Summary",
        "",
        f"- Official trusted: `{legitimacy.get('official_trusted', 0)}`",
        f"- Owned trusted: `{legitimacy.get('owned_trusted', 0)}`",
        f"- Needs review: `{legitimacy.get('needs_review', 0)}`",
        f"- Blocked hostile: `{legitimacy.get('blocked_hostile', 0)}`",
        "",
        "## Advisor Note",
        "",
        PUBLIC_CATALOG_ADVISOR_NOTE,
        "",
        "## Interop Surfaces",
        "",
        "| Surface | Scope | Presence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in interop_sources:
        lines.append(
            "| `{source_id}` | `{compatibility_surface}` | `{local_presence}` | {notes} |".format(
                source_id=row.get("source_id", ""),
                compatibility_surface=row.get("compatibility_surface", ""),
                local_presence=row.get("local_presence", ""),
                notes=", ".join(str(item) for item in row.get("notes", [])),
            )
        )
    lines.extend(
        [
            "",
            "## Current Sources",
            "",
            "Source-level `recommended_action` values describe intake posture for whole upstream/source buckets.",
            "They do not override the legitimacy state already assigned to installed skills in the matrix below.",
            "",
        "| Source | Type | Origin | Version | Presence | Risk | Action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in sources:
        lines.append(
            "| `{source_id}` | `{source_type}` | `{origin}` | `{version_or_commit}` | `{local_presence}` | `{risk_class}` | `{recommended_action}` |".format(
                **row
            )
        )
    if recent_work:
        lines.extend(
            [
                "",
                "## Recent-Work Skills",
                "",
                ", ".join(f"`{name}`" for name in recent_work),
            ]
        )
    lines.extend(
        [
            "",
            "## Current Skill Matrix",
            "",
            "| Skill | Source Type | Ownership | Legitimacy | Presence | Drift | Risk | Action | Author | Canonical Source |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in skills:
        render_row = dict(row)
        render_row["author"] = _md_cell(row.get("author"))
        render_row["canonical_source"] = _md_cell(row.get("canonical_source"))
        lines.append(
            "| `{name}` | `{source_type}` | `{ownership}` | `{legitimacy_status}` | `{local_presence}` | `{drift_state}` | `{risk_class}` | `{recommended_action}` | {author} | {canonical_source} |".format(
                **render_row
            )
        )
    if incidents:
        lines.extend(
            [
                "",
                "## Active Incidents",
                "",
                "| Severity | Subject | Ownership | Legitimacy | Summary |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in incidents:
            lines.append("| `{severity}` | `{subject}` | `{ownership}` | `{legitimacy_status}` | {summary} |".format(**row))
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_inventory_snapshot()
    output = render_catalog(payload)
    generated_at = os.environ.get("SKILL_CATALOG_GENERATED_AT") or str(payload.get("generated_at", ""))
    repo_catalog_output = render_repo_catalog(repo_root=REPO_ROOT, generated_at=generated_at)
    references_root = REPO_ROOT / "references"
    repo_catalog_target = REPO_ROOT / "skill-catalog.md"
    catalog_target = references_root / "skill-catalog.md"
    matrix_target = references_root / "vscode-codex-skill-update-matrix.md"
    repo_catalog_target.write_text(repo_catalog_output, encoding="utf-8")
    catalog_target.write_text(output, encoding="utf-8")
    # Keep both inventory-facing views in lockstep so repo-owned docs do not drift.
    matrix_target.write_text(render_vscode_matrix(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
