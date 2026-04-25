from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_iso(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        return text
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", text):
        return text
    return None


def unique_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def lane_rollup(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter()
    next_actions: list[str] = []
    artifacts: list[str] = []
    compact_lanes: list[dict[str, Any]] = []
    for lane in lanes:
        name = str(lane.get("name", "")).strip()
        status = str(lane.get("status", "unknown")).strip() or "unknown"
        next_step = str(lane.get("next_step", "")).strip()
        lane_artifacts = [str(item) for item in lane.get("artifacts", []) if str(item).strip()]
        status_counts[status] += 1
        if next_step:
            next_actions.append(f"{name}: {next_step}")
        artifacts.extend(lane_artifacts)
        compact_lanes.append(
            {
                "name": name,
                "status": status,
                "next_step": next_step,
                "artifact_count": len(lane_artifacts),
            }
        )
    overall_status = "unknown"
    if status_counts.get("in_progress"):
        overall_status = "in_progress"
    elif status_counts.get("pending"):
        overall_status = "pending"
    elif status_counts:
        overall_status = "completed"
    return {
        "overall_status": overall_status,
        "status_counts": dict(status_counts),
        "next_actions": unique_list(next_actions),
        "artifacts": unique_list(artifacts),
        "lanes": compact_lanes,
    }


def parse_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def extract_tags(path: Path, title: str) -> list[str]:
    source = f"{path.stem} {title}".lower()
    tags: list[str] = []
    for token in ("penny", "media", "image", "skill", "audit", "vrm", "mx3", "shim", "megaquest", "cyberpunk"):
        if token in source:
            tags.append(token)
    return unique_list(tags)


def build_workstream_entry(path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    task = str(data.get("task", "")).strip()
    lanes = data.get("lanes")
    if not task or not isinstance(lanes, list):
        return None
    rollup = lane_rollup([lane for lane in lanes if isinstance(lane, dict)])
    updated_at = normalize_iso(data.get("updated_at")) or path_mtime_iso(path)
    created_at = normalize_iso(data.get("created_at"))
    return {
        "entry_id": path.stem,
        "kind": "workstream_state",
        "title": task,
        "status": rollup["overall_status"],
        "updated_at": updated_at,
        "created_at": created_at,
        "source_path": str(path),
        "tags": extract_tags(path, task),
        "next_actions": rollup["next_actions"],
        "artifacts": rollup["artifacts"],
        "lane_status_counts": rollup["status_counts"],
        "lanes": rollup["lanes"],
    }


def build_resume_contract_entry(path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    task = str(data.get("task", "")).strip()
    resume_contract = data.get("resume_contract")
    if not task or not isinstance(resume_contract, dict):
        return None
    current_focus = str(resume_contract.get("current_focus", "")).strip()
    next_lane = str(resume_contract.get("next_lane", "")).strip()
    next_actions = unique_list([item for item in (current_focus, next_lane) if item])
    return {
        "entry_id": path.stem,
        "kind": "resume_contract",
        "title": task,
        "status": "resume_ready",
        "updated_at": path_mtime_iso(path),
        "created_at": None,
        "source_path": str(path),
        "tags": extract_tags(path, task),
        "next_actions": next_actions,
        "artifacts": [str(resume_contract.get("state_file", "")).strip()] if str(resume_contract.get("state_file", "")).strip() else [],
        "lane_status_counts": {},
        "lanes": [],
    }


def build_quest_report_entry(path: Path, data: dict[str, Any]) -> dict[str, Any] | None:
    quest = data.get("quest")
    if not isinstance(quest, dict):
        return None
    title = str(quest.get("title") or quest.get("task") or path.stem).strip()
    deliverables = [str(item) for item in quest.get("deliverables", []) if str(item).strip()]
    evidence = [str(item) for item in quest.get("evidence", []) if str(item).strip()]
    checkpoints = [item for item in quest.get("checkpoints", []) if isinstance(item, dict)]
    next_actions = []
    for step in quest.get("steps", []):
        if isinstance(step, dict) and str(step.get("status", "")).strip().lower() != "done":
            label = str(step.get("label", "")).strip()
            if label:
                next_actions.append(label)
    updated_candidates = [
        normalize_iso(quest.get("completed_at")),
        normalize_iso(quest.get("updated_at")),
    ] + [normalize_iso(item.get("created_at")) for item in checkpoints]
    updated_at = next((item for item in updated_candidates if item), None) or path_mtime_iso(path)
    return {
        "entry_id": path.stem,
        "kind": "quest_report",
        "title": title,
        "status": str(quest.get("outcome", "recorded")).strip() or "recorded",
        "updated_at": updated_at,
        "created_at": None,
        "source_path": str(path),
        "tags": extract_tags(path, title),
        "next_actions": unique_list(next_actions),
        "artifacts": unique_list(deliverables + evidence),
        "lane_status_counts": {},
        "lanes": [],
    }


def build_note_entry(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    lines = [line.rstrip() for line in raw.splitlines()]
    meaningful = [line for line in lines if line.strip() and line.strip() != "# Next Quest"]
    preview = " ".join(meaningful[:3]).strip()
    return {
        "note_date": path.parent.name,
        "source_path": str(path),
        "updated_at": path_mtime_iso(path),
        "is_blank": not meaningful,
        "preview": preview,
    }


def build_registry(reports_root: Path, workstreams_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []
    skipped_json: list[str] = []

    for path in sorted(workstreams_root.glob("*quest*.json")):
        data = parse_json(path)
        if not isinstance(data, dict):
            skipped_json.append(str(path))
            continue
        entry = (
            build_workstream_entry(path, data)
            or build_quest_report_entry(path, data)
            or build_resume_contract_entry(path, data)
        )
        if entry:
            entries.append(entry)
        else:
            skipped_json.append(str(path))

    for path in sorted(reports_root.rglob("next_quest.md")):
        notes.append(build_note_entry(path))

    entries.sort(key=lambda item: (item.get("updated_at") or "", item["source_path"]), reverse=True)
    notes.sort(key=lambda item: item["note_date"], reverse=True)

    summary = {
        "total_entries": len(entries),
        "workstream_states": sum(1 for item in entries if item["kind"] == "workstream_state"),
        "quest_reports": sum(1 for item in entries if item["kind"] == "quest_report"),
        "resume_contracts": sum(1 for item in entries if item["kind"] == "resume_contract"),
        "next_quest_notes": len(notes),
        "nonempty_next_quest_notes": sum(1 for item in notes if not item["is_blank"]),
        "blank_next_quest_notes": sum(1 for item in notes if item["is_blank"]),
        "skipped_json_files": len(skipped_json),
    }

    return {
        "generated_at": iso_now(),
        "sources": {
            "reports_root": str(reports_root),
            "workstreams_root": str(workstreams_root),
        },
        "summary": summary,
        "entries": entries,
        "notes": notes,
        "skipped_json": skipped_json,
    }


def render_markdown(registry: dict[str, Any]) -> str:
    lines = [
        "# Quest Registry",
        "",
        f"Generated at: {registry['generated_at']}",
        "",
        "## Summary",
        f"- total quest entries: {registry['summary']['total_entries']}",
        f"- workstream states: {registry['summary']['workstream_states']}",
        f"- quest reports: {registry['summary']['quest_reports']}",
        f"- resume contracts: {registry['summary']['resume_contracts']}",
        f"- next_quest notes: {registry['summary']['next_quest_notes']}",
        f"- non-empty next_quest notes: {registry['summary']['nonempty_next_quest_notes']}",
        f"- blank next_quest notes: {registry['summary']['blank_next_quest_notes']}",
        f"- skipped quest-named JSON files: {registry['summary']['skipped_json_files']}",
        "",
        "## Entries",
    ]
    for entry in registry["entries"]:
        lines.extend(
            [
                "",
                f"### {entry['title']}",
                f"- kind: {entry['kind']}",
                f"- status: {entry['status']}",
                f"- updated_at: {entry['updated_at']}",
                f"- source: `{entry['source_path']}`",
            ]
        )
        if entry["tags"]:
            lines.append(f"- tags: {', '.join(entry['tags'])}")
        if entry["lane_status_counts"]:
            status_text = ", ".join(f"{key}={value}" for key, value in sorted(entry["lane_status_counts"].items()))
            lines.append(f"- lane counts: {status_text}")
        if entry["next_actions"]:
            lines.append(f"- next actions: {' | '.join(entry['next_actions'])}")
        if entry["artifacts"]:
            lines.append(f"- artifacts: {' | '.join(entry['artifacts'])}")

    lines.extend(["", "## next_quest Notes"])
    for note in registry["notes"]:
        preview = note["preview"] if note["preview"] else "(blank)"
        lines.extend(
            [
                "",
                f"### {note['note_date']}",
                f"- source: `{note['source_path']}`",
                f"- blank: {str(note['is_blank']).lower()}",
                f"- preview: {preview}",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    references_root = skill_root / "references"
    parser = argparse.ArgumentParser(description="Build a registry of prior and active quest artifacts.")
    parser.add_argument("--reports-root", type=Path, default=Path(r"<PRIVATE_REPO_ROOT>\reports"))
    parser.add_argument("--workstreams-root", type=Path, default=Path(r"%USERPROFILE%\.codex\workstreams"))
    parser.add_argument("--json-out", type=Path, default=references_root / "quest-registry.generated.json")
    parser.add_argument("--md-out", type=Path, default=references_root / "quest-registry.generated.md")
    args = parser.parse_args()

    registry = build_registry(args.reports_root, args.workstreams_root)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(registry), encoding="utf-8")
    print(json.dumps({"json_out": str(args.json_out), "md_out": str(args.md_out), "total_entries": registry["summary"]["total_entries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
