#!/usr/bin/env python3
"""Shared runtime helpers for the local heterogeneous media pipeline."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


JOB_TYPES = {
    "text_to_still",
    "still_to_motion",
    "keyframe_range_to_motion",
    "motion_to_spoken",
    "repair_or_upscale",
    "full_text_to_mp4",
}

EVENT_TYPES = {
    "job.created",
    "slice.queued",
    "slice.started",
    "slice.completed",
    "review.queued",
    "review.completed",
    "mx3.qc.completed",
    "retry.queued",
    "candidate.selected",
    "baseline.promoted",
    "archive.moved",
}

EVENT_LOG_NAME = "events.ndjson"
MANIFEST_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def default_voice_profile(
    *,
    voice_id: str | None = None,
    language: str | None = None,
    speed: float | None = None,
    pitch_shift: float | None = None,
) -> dict[str, Any]:
    return {
        "voice_id": voice_id,
        "language": language,
        "speed": speed,
        "pitch_shift": pitch_shift,
    }


def infer_job_type(
    source: Path,
    *,
    requested: str | None = None,
    expected_dialogue: str = "",
) -> str:
    if requested:
        normalized = requested.strip()
        if normalized not in JOB_TYPES:
            raise ValueError(f"Unsupported job_type: {requested}")
        return normalized
    suffix = source.suffix.lower()
    if expected_dialogue.strip():
        return "full_text_to_mp4"
    if suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        return "motion_to_spoken"
    return "still_to_motion"


def ensure_event_log(sidecar_dir: Path) -> Path:
    event_log = sidecar_dir / EVENT_LOG_NAME
    event_log.parent.mkdir(parents=True, exist_ok=True)
    if not event_log.exists():
        event_log.write_text("", encoding="utf-8")
    return event_log


def manifest_defaults(
    *,
    job_type: str,
    subject: str,
    continuity_profile: str,
    source_reference: str,
    copied_source_reference: str | None,
    expected_dialogue: str = "",
    notes: str = "",
    voice_profile: dict[str, Any] | None = None,
    event_log_path: str | None = None,
) -> dict[str, Any]:
    return {
        "job_type": job_type,
        "subject": subject,
        "persona_lock": {
            "subject": subject,
            "continuity_profile": continuity_profile,
            "canonical": subject.lower() == "penny",
        },
        "approved_references": [
            {
                "source_reference": source_reference,
                "copied_source_reference": copied_source_reference,
                "role": "primary_baseline",
            }
        ],
        "voice_profile": voice_profile or default_voice_profile(),
        "lane_assignments": {
            "raw_render": {},
            "review": {},
            "qc": {},
            "speech": {},
            "editorial": {},
        },
        "slice_timing_budget": {
            "target_max_minutes": 30.0,
            "lanes": {},
        },
        "segments": [],
        "qc_state": {
            "review_mode": "per_slice_event_driven",
            "review_started_immediately": True,
            "per_slice": {},
            "accepted_candidates": [],
            "rejected_candidates": [],
            "baseline_locked_to_voice": None,
        },
        "retry_lineage": [],
        "final_export_selection": {},
        "event_log_path": event_log_path,
        "event_counters": {},
        "last_event": None,
        "notes": notes,
        "expected_dialogue": expected_dialogue,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_manifest_fields(
    manifest: dict[str, Any],
    *,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    merged = deepcopy(manifest)
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = deepcopy(value)
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**deepcopy(value), **merged[key]}
            for nested_key, nested_value in value.items():
                if (
                    isinstance(nested_value, dict)
                    and isinstance(merged[key].get(nested_key), dict)
                ):
                    merged[key][nested_key] = {
                        **deepcopy(nested_value),
                        **merged[key][nested_key],
                    }
    return merged


def update_manifest(path: Path, mutator: Callable[[dict[str, Any]], dict[str, Any] | None]) -> dict[str, Any]:
    with MANIFEST_LOCK:
        manifest = load_manifest(path)
        updated = mutator(deepcopy(manifest))
        if updated is None:
            updated = manifest
        save_manifest(path, updated)
        return updated


def append_event(
    event_log_path: Path,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    phase: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unsupported event type: {event_type}")
    record = {
        "created_at": now_iso(),
        "event_type": event_type,
        "phase": phase,
        "status": status,
        "payload": payload or {},
    }
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    with event_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return record


def emit_manifest_event(
    manifest_path: Path,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    phase: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    payload = payload or {}

    def mutator(manifest: dict[str, Any]) -> dict[str, Any]:
        event_log_path = Path(str(manifest.get("event_log_path") or manifest_path.parent / EVENT_LOG_NAME))
        ensure_event_log(event_log_path.parent)
        event_record = append_event(event_log_path, event_type, payload, phase=phase, status=status)
        counters = manifest.setdefault("event_counters", {})
        counters[event_type] = int(counters.get(event_type, 0)) + 1
        manifest["event_log_path"] = str(event_log_path)
        manifest["last_event"] = event_record
        return manifest

    updated = update_manifest(manifest_path, mutator)
    return dict(updated.get("last_event") or {})


def register_segment_plan(manifest_path: Path, segments: list[dict[str, Any]]) -> dict[str, Any]:
    def mutator(manifest: dict[str, Any]) -> dict[str, Any]:
        manifest["segments"] = deepcopy(segments)
        qc_state = manifest.setdefault("qc_state", {})
        qc_state.setdefault("per_slice", {})
        for segment in segments:
            idx = str(segment.get("index"))
            qc_state["per_slice"].setdefault(
                idx,
                {
                    "status": "queued",
                    "raw_review": None,
                    "multilane_review_json": None,
                    "multilane_review_md": None,
                    "shockwave_review": None,
                    "mx3_review": None,
                    "review_decision": None,
                    "retry_suggestion": None,
                },
            )
        return manifest

    return update_manifest(manifest_path, mutator)


def update_segment_state(manifest_path: Path, segment_index: int, patch: dict[str, Any]) -> dict[str, Any]:
    key = str(segment_index)

    def mutator(manifest: dict[str, Any]) -> dict[str, Any]:
        for segment in manifest.setdefault("segments", []):
            if int(segment.get("index") or 0) == segment_index:
                segment.update(patch)
        qc_state = manifest.setdefault("qc_state", {}).setdefault("per_slice", {})
        qc_entry = qc_state.setdefault(key, {})
        qc_entry.update(patch)
        return manifest

    return update_manifest(manifest_path, mutator)


def append_retry_lineage(
    manifest_path: Path,
    *,
    segment_index: int | None,
    reason: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "recorded_at": now_iso(),
        "segment_index": segment_index,
        "reason": reason,
        "context": context or {},
    }

    def mutator(manifest: dict[str, Any]) -> dict[str, Any]:
        manifest.setdefault("retry_lineage", []).append(payload)
        return manifest

    return update_manifest(manifest_path, mutator)


def set_final_export_selection(
    manifest_path: Path,
    *,
    export_path: Path,
    export_kind: str,
    review_decision: str,
    notes: str | None = None,
) -> dict[str, Any]:
    def mutator(manifest: dict[str, Any]) -> dict[str, Any]:
        manifest["final_export_selection"] = {
            "selected_at": now_iso(),
            "export_path": str(export_path),
            "export_kind": export_kind,
            "review_decision": review_decision,
            "notes": notes,
        }
        return manifest

    return update_manifest(manifest_path, mutator)
