#!/usr/bin/env python3
"""Audit the Cybertron fabric host ops candidate package."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import sys


REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/admission-workflow.md",
    "references/host-readiness.md",
    "references/repo-parity.md",
    "references/model-matrix.md",
    "scripts/cybertron_fabric_host_audit.py",
    "scripts/cybertron_repo_parity.py",
    "scripts/cybertron_model_matrix_check.py",
    "scripts/cybertron_host_readiness.py",
]


@dataclass
class AuditReport:
    root: str
    skill_name: str
    description: str
    missing_files: list[str]
    notes: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Cybertron fabric host ops candidate package")
    parser.add_argument(
        "--skill-root",
        default="skill-candidates/cybertron-fabric-host-ops",
        help="Path to the skill candidate root",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def read_skill_metadata(skill_md: Path) -> tuple[str, str]:
    name = ""
    description = ""
    if not skill_md.is_file():
        return name, description

    in_frontmatter = False
    for raw_line in skill_md.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if not in_frontmatter or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if key == "name":
            name = value
        elif key == "description":
            description = value
    return name, description


def main() -> int:
    args = parse_args()
    root = Path(args.skill_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: skill root not found: {root}", file=sys.stderr)
        return 2

    missing = [item for item in REQUIRED_FILES if not (root / item).is_file()]
    skill_name, description = read_skill_metadata(root / "SKILL.md")

    notes: list[str] = []
    if skill_name != "cybertron-fabric-host-ops":
        notes.append(f"frontmatter-name={skill_name or '<missing>'}")
    if "Cybertron" not in description:
        notes.append("description-missing-Cybertron")
    if "host" not in description.lower():
        notes.append("description-missing-host-scope")

    report = AuditReport(
        root=str(root),
        skill_name=skill_name,
        description=description,
        missing_files=missing,
        notes=notes,
    )
    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if missing:
        print(f"audit: missing {len(missing)} required file(s)")
        for item in missing:
            print(f"missing:{item}")
        return 1

    if notes:
        print("audit: candidate present with notes")
        for item in notes:
            print(f"note:{item}")
    else:
        print("audit: candidate package looks complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
