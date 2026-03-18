#!/usr/bin/env python3
"""Prepare forward/reverse loop assets and a CapCut handoff manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a CapCut loop handoff from an approved forward clip")
    parser.add_argument("input", type=Path, help="Approved forward video clip")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output folder")
    parser.add_argument("--run-name", required=True, help="Base name for the handoff files")
    parser.add_argument("--trim-edges", action="store_true", help="Trim first/last frame from the reversed leg")
    return parser.parse_args()


def ffprobe_frames(video: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return int((result.stdout or "0").strip() or "0")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    forward_path = args.out_dir / f"{args.run_name}_forward.mp4"
    reverse_path = args.out_dir / f"{args.run_name}_reverse.mp4"
    manifest_path = args.out_dir / f"{args.run_name}_capcut_handoff.json"

    shutil.copy2(args.input, forward_path)

    if args.trim_edges:
        frame_count = ffprobe_frames(args.input)
        reverse_source = args.out_dir / f"{args.run_name}_reverse_source.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(args.input), "-vf", "reverse", "-an", str(reverse_source)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(reverse_source),
                "-vf",
                f"trim=start_frame=1:end_frame={max(frame_count - 1, 2)}",
                "-an",
                str(reverse_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        reverse_source.unlink(missing_ok=True)
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(args.input), "-vf", "reverse", "-an", str(reverse_path)],
            check=True,
            capture_output=True,
            text=True,
        )

    manifest = {
        "run_name": args.run_name,
        "forward_clip": str(forward_path),
        "reverse_clip": str(reverse_path),
        "editor_target": "CapCut",
        "sequence_order": [str(forward_path), str(reverse_path)],
        "notes": [
            "Import the forward clip first and the reversed clip second.",
            "Butt-join them or add a tiny dissolve only if the seam feels abrupt.",
            "If timing still reads slow, speed-ramp or slightly trim the forward leg in the editor instead of rerendering the reverse leg first.",
            "Keep the original approved forward clip unchanged for archive lineage.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
