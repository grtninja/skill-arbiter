#!/usr/bin/env python3
"""Initialize a deterministic Penny media work item folder."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

from local_defaults import DEFAULT_WORK_ITEMS
from media_pipeline_runtime import (
    default_voice_profile,
    emit_manifest_event,
    ensure_event_log,
    ensure_manifest_fields,
    infer_job_type,
    manifest_defaults,
    save_manifest,
)


PHASE_DIRS = [
    "00_reference_approved",
    "01_staged",
    "02_raw_forward",
    "03_review",
    "04_vfi_master",
    "05_audio_tts",
    "06_lipsync",
    "07_asr_qc",
    "08_capcut_handoff",
    "09_exports",
    "10_sidecars",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a high-quality Penny media work item")
    parser.add_argument("source", type=Path, help="Approved source image or video")
    parser.add_argument("--job-name", required=True, help="Short human-readable job name")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_WORK_ITEMS,
        help="Root folder for work items",
    )
    parser.add_argument("--subject", default="Penny", help="Subject name")
    parser.add_argument("--continuity-profile", default="penny_canon_v1", help="Continuity profile id")
    parser.add_argument("--job-type", default=None, help="Explicit pipeline job type")
    parser.add_argument("--expected-dialogue", default="", help="Optional expected spoken line")
    parser.add_argument("--notes", default="", help="Optional operator notes")
    parser.add_argument("--voice-id", default=None, help="Canonical voice id for spoken jobs")
    parser.add_argument("--voice-language", default=None, help="Canonical voice language")
    parser.add_argument("--voice-speed", type=float, default=None, help="Canonical voice speed")
    parser.add_argument("--voice-pitch-shift", type=float, default=None, help="Canonical voice pitch shift")
    parser.add_argument("--no-copy-source", action="store_true", help="Do not copy the source into the work item")
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return slug or "work_item"


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"Source does not exist: {args.source}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_slug = slugify(args.job_name)
    job_dir = args.root / f"{timestamp}_{job_slug}"
    job_dir.mkdir(parents=True, exist_ok=False)

    for name in PHASE_DIRS:
        (job_dir / name).mkdir(parents=True, exist_ok=True)

    copied_source: str | None = None
    if not args.no_copy_source:
        target = job_dir / "00_reference_approved" / args.source.name
        shutil.copy2(args.source, target)
        copied_source = str(target)

    sidecar_dir = job_dir / "10_sidecars"
    event_log_path = ensure_event_log(sidecar_dir)
    job_type = infer_job_type(args.source, requested=args.job_type, expected_dialogue=args.expected_dialogue)
    voice_profile = default_voice_profile(
        voice_id=args.voice_id,
        language=args.voice_language,
        speed=args.voice_speed,
        pitch_shift=args.voice_pitch_shift,
    )

    manifest = ensure_manifest_fields(
        {
        "job_name": args.job_name,
        "job_slug": job_slug,
        "created_at_local": datetime.now().astimezone().isoformat(),
        "continuity_profile": args.continuity_profile,
        "source_reference": str(args.source),
        "copied_source_reference": copied_source,
        "phase_dirs": PHASE_DIRS,
        "status": {
            "source_locked": True,
            "raw_forward_complete": False,
            "review_complete": False,
            "vfi_master_complete": False,
            "tts_complete": False,
            "lipsync_complete": False,
            "asr_qc_complete": False,
            "capcut_handoff_complete": False,
            "final_export_complete": False,
        },
        },
        defaults=manifest_defaults(
            job_type=job_type,
            subject=args.subject,
            continuity_profile=args.continuity_profile,
            source_reference=str(args.source),
            copied_source_reference=copied_source,
            expected_dialogue=args.expected_dialogue,
            notes=args.notes,
            voice_profile=voice_profile,
            event_log_path=str(event_log_path),
        ),
    )

    manifest_path = sidecar_dir / "job_manifest.json"
    save_manifest(manifest_path, manifest)
    emit_manifest_event(
        manifest_path,
        "job.created",
        {
            "job_name": args.job_name,
            "job_slug": job_slug,
            "job_type": job_type,
            "subject": args.subject,
            "source_reference": str(args.source),
            "copied_source_reference": copied_source,
        },
        phase="job",
        status="created",
    )

    checklist = sidecar_dir / "next_steps.txt"
    checklist.write_text(
        "\n".join(
            [
                "1. Stage a safe render input into 01_staged.",
                "2. Generate a forward-only native Wan clip into 02_raw_forward.",
                "3. Build and inspect a review sheet in 03_review.",
                "4. Master the approved forward clip into 04_vfi_master.",
                "5. Put TTS or approved dialogue audio into 05_audio_tts.",
                "6. Put lip-sync outputs into 06_lipsync.",
                "7. Run ASR QC and save outputs into 07_asr_qc.",
                "8. Prepare loop/editor handoff in 08_capcut_handoff.",
                "9. Save final exports into 09_exports.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
