#!/usr/bin/env python3
"""Create a higher-fps looped master from a rendered clip."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a looped, interpolated, upscaled video master")
    parser.add_argument("input", type=Path, help="Input video")
    parser.add_argument("output", type=Path, help="Output mastered video")
    parser.add_argument("--target-fps", type=int, default=12, help="Target output fps after interpolation")
    parser.add_argument("--scale-width", type=int, default=768, help="Output width")
    parser.add_argument("--scale-height", type=int, default=1344, help="Output height")
    parser.add_argument("--crf", type=int, default=18, help="x264 CRF")
    parser.add_argument("--preset", default="slow", help="x264 preset")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON summary path")
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame_count = ffprobe_frames(args.input)
    if frame_count < 3:
        raise SystemExit("Need at least 3 frames to build a loop master")

    with tempfile.TemporaryDirectory(prefix="loop-master-") as tmpdir:
        reverse_source = Path(tmpdir) / "reverse_source.mp4"
        reverse_clip = Path(tmpdir) / "reverse_trimmed.mp4"
        list_path = Path(tmpdir) / "concat.txt"
        raw_loop = Path(tmpdir) / "raw_loop.mp4"

        # Trim off the first and last frames from the reversed leg to avoid a visible hold at the turn.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(args.input),
                "-vf",
                "reverse",
                "-an",
                str(reverse_source),
            ],
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
                "trim=start_frame=1:end_frame={end}".format(end=max(frame_count - 1, 2)),
                "-an",
                str(reverse_clip),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        list_path.write_text(
            "file '{a}'\nfile '{b}'\n".format(
                a=str(args.input).replace("'", "'\\''"),
                b=str(reverse_clip).replace("'", "'\\''"),
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(raw_loop),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        filter_chain = (
            "minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
            "scale={w}:{h}:flags=lanczos,format=yuv420p"
        ).format(fps=args.target_fps, w=args.scale_width, h=args.scale_height)

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_loop),
                "-vf",
                filter_chain,
                "-c:v",
                "libx264",
                "-preset",
                args.preset,
                "-crf",
                str(args.crf),
                "-pix_fmt",
                "yuv420p",
                str(args.output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    summary = {
        "input": str(args.input),
        "output": str(args.output),
        "frame_count": frame_count,
        "target_fps": args.target_fps,
        "scale_width": args.scale_width,
        "scale_height": args.scale_height,
        "notes": [
            "loop is built as a ping-pong master from the forward clip and a trimmed reversed leg",
            "fps increase uses ffmpeg minterpolate",
            "final upscale uses lanczos because AMUSE RealESRGAN was not available in this run",
        ],
    }
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
