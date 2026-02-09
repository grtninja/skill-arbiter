#!/usr/bin/env python3
"""Inspect skill dependency and fan-out risk from SKILL metadata."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

SKILL_RE = re.compile(r"\$([a-z0-9][a-z0-9-]{0,63})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect skill dependency graph and fan-out risk")
    parser.add_argument("--skills-root", default="skill-candidates", help="Skills root directory")
    parser.add_argument("--skill", action="append", default=[], help="Optional skill name filter (repeatable)")
    parser.add_argument(
        "--include-plain-names",
        action="store_true",
        help="Also match plain skill-name mentions in SKILL.md text",
    )
    parser.add_argument("--fanout-threshold", type=int, default=4, help="Out-degree hotspot threshold")
    parser.add_argument("--transitive-threshold", type=int, default=12, help="Transitive reach risk threshold")
    parser.add_argument("--json-out", default="", help="Optional JSON report output path")
    parser.add_argument("--dot-out", default="", help="Optional DOT graph output path")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def find_skill_dirs(skills_root: Path, filters: set[str]) -> dict[str, Path]:
    results: dict[str, Path] = {}
    for child in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        skill_name = child.name
        if filters and skill_name not in filters:
            continue
        if (child / "SKILL.md").is_file():
            results[skill_name] = child
    return results


def extract_plain_dependencies(text: str, skill_names: set[str], self_name: str) -> set[str]:
    deps: set[str] = set()
    for name in skill_names:
        if name == self_name:
            continue
        pattern = re.compile(rf"(?<![a-z0-9-]){re.escape(name)}(?![a-z0-9-])")
        if pattern.search(text):
            deps.add(name)
    return deps


def parse_dependencies(
    skill_name: str,
    skill_path: Path,
    known_names: set[str],
    include_plain_names: bool,
) -> tuple[set[str], list[dict[str, str]]]:
    skill_text = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    deps: set[str] = set()
    edges: list[dict[str, str]] = []

    for match in SKILL_RE.findall(skill_text):
        dep = str(match).strip()
        if dep == skill_name:
            continue
        if dep in known_names:
            deps.add(dep)
            edges.append({"from": skill_name, "to": dep, "type": "explicit_dollar"})

    if include_plain_names:
        for dep in sorted(extract_plain_dependencies(skill_text, known_names, skill_name)):
            if dep in deps:
                continue
            deps.add(dep)
            edges.append({"from": skill_name, "to": dep, "type": "plain_name"})

    return deps, edges


def build_in_degree(adjacency: dict[str, set[str]]) -> dict[str, int]:
    values = {name: 0 for name in adjacency}
    for deps in adjacency.values():
        for dep in deps:
            values[dep] = values.get(dep, 0) + 1
    return values


def transitive_reach(start: str, adjacency: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(adjacency.get(start, set()))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(sorted(adjacency.get(node, set())))
    return seen


def detect_cycles(adjacency: dict[str, set[str]]) -> list[list[str]]:
    cycles: set[tuple[str, ...]] = set()
    stack: list[str] = []
    on_stack: set[str] = set()
    visited: set[str] = set()

    def _visit(node: str) -> None:
        visited.add(node)
        stack.append(node)
        on_stack.add(node)

        for nxt in sorted(adjacency.get(node, set())):
            if nxt not in visited:
                _visit(nxt)
                continue
            if nxt not in on_stack:
                continue

            index = stack.index(nxt)
            cycle = stack[index:] + [nxt]
            if len(cycle) < 3:
                continue

            body = cycle[:-1]
            minimum = min(body)
            min_index = body.index(minimum)
            rotated = body[min_index:] + body[:min_index]
            normalized = tuple(rotated + [rotated[0]])
            cycles.add(normalized)

        stack.pop()
        on_stack.remove(node)

    for node in sorted(adjacency.keys()):
        if node not in visited:
            _visit(node)

    return [list(item) for item in sorted(cycles)]


def render_table(report: dict[str, Any]) -> str:
    lines = [
        "skills_root: {skills_root}".format(**report),
        "nodes={node_count} edges={edge_count} cycles={cycle_count}".format(**report["graph"]),
        "max_out_degree={max_out_degree} max_in_degree={max_in_degree}".format(**report["metrics"]),
        "",
        "fan-out hotspots:",
    ]
    if report["fanout_hotspots"]:
        for row in report["fanout_hotspots"]:
            lines.append(f"- {row['skill']}: out_degree={row['out_degree']} deps={','.join(row['dependencies'])}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("n+1 risks:")
    if report["n_plus_one_risks"]:
        for row in report["n_plus_one_risks"]:
            lines.append(
                f"- {row['skill']}: transitive_reach={row['transitive_reach']} out_degree={row['out_degree']}"
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("cycles:")
    if report["cycles"]:
        for cycle in report["cycles"]:
            lines.append(f"- {' -> '.join(cycle)}")
    else:
        lines.append("- none")

    return "\n".join(lines)


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_dot(path_text: str, skills: list[str], edges: list[dict[str, str]]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["digraph skill_dependencies {", "  rankdir=LR;"]
    for skill in skills:
        lines.append(f'  "{skill}";')
    for edge in edges:
        label = edge["type"]
        lines.append(f'  "{edge["from"]}" -> "{edge["to"]}" [label="{label}"];')
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    if not skills_root.is_dir():
        raise FileNotFoundError(f"skills root not found: {skills_root}")

    filters = {str(item).strip() for item in args.skill if str(item).strip()}
    skills = find_skill_dirs(skills_root, filters)
    if not skills:
        raise ValueError("no skills found")

    names = set(skills.keys())
    adjacency: dict[str, set[str]] = {name: set() for name in skills}
    edges: list[dict[str, str]] = []

    for name, path in skills.items():
        deps, new_edges = parse_dependencies(name, path, names, bool(args.include_plain_names))
        adjacency[name] = set(sorted(deps))
        edges.extend(new_edges)

    in_degree = build_in_degree(adjacency)
    out_degree = {name: len(deps) for name, deps in adjacency.items()}

    reach_rows: list[dict[str, Any]] = []
    for name in sorted(adjacency.keys()):
        reach = transitive_reach(name, adjacency)
        reach_rows.append(
            {
                "skill": name,
                "transitive_reach": len(reach),
                "out_degree": out_degree.get(name, 0),
            }
        )

    fanout_hotspots = [
        {
            "skill": name,
            "out_degree": out_degree[name],
            "dependencies": sorted(adjacency[name]),
        }
        for name in sorted(adjacency.keys())
        if out_degree[name] >= max(int(args.fanout_threshold), 1)
    ]

    n_plus_one = [
        row
        for row in sorted(reach_rows, key=lambda item: (-item["transitive_reach"], -item["out_degree"], item["skill"]))
        if row["transitive_reach"] >= max(int(args.transitive_threshold), 1)
    ]

    cycles = detect_cycles(adjacency)

    recommendations: list[str] = []
    if fanout_hotspots:
        recommendations.append("Reduce broad trigger prompts for high out-degree skills and split responsibilities.")
    if n_plus_one:
        recommendations.append("Introduce guardrails to cap transitive skill chains for high-reach nodes.")
    if cycles:
        recommendations.append("Break cyclic dependencies to avoid recursive invocation loops.")
    if not recommendations:
        recommendations.append("Graph is stable under current thresholds.")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "skills_root": str(skills_root),
        "graph": {
            "node_count": len(skills),
            "edge_count": len(edges),
            "cycle_count": len(cycles),
        },
        "metrics": {
            "max_out_degree": max(out_degree.values()) if out_degree else 0,
            "max_in_degree": max(in_degree.values()) if in_degree else 0,
            "fanout_threshold": max(int(args.fanout_threshold), 1),
            "transitive_threshold": max(int(args.transitive_threshold), 1),
        },
        "nodes": sorted(skills.keys()),
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"], item["type"])),
        "out_degree": [
            {"skill": name, "out_degree": out_degree[name]} for name in sorted(out_degree.keys(), key=lambda item: (-out_degree[item], item))
        ],
        "in_degree": [
            {"skill": name, "in_degree": in_degree.get(name, 0)} for name in sorted(in_degree.keys(), key=lambda item: (-in_degree[item], item))
        ],
        "fanout_hotspots": fanout_hotspots,
        "n_plus_one_risks": n_plus_one,
        "cycles": cycles,
        "recommendations": recommendations,
    }

    write_json(args.json_out, report)
    write_dot(args.dot_out, sorted(skills.keys()), report["edges"])

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(render_table(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
