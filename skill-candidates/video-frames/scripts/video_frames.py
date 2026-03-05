#!/usr/bin/env python3
"""Extract frames and short clips from local videos with ffmpeg."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    raise RuntimeError("ffmpeg not found on PATH")


def require_input_file(path_text: str) -> Path:
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"input file not found: {path}")
    return path


def prepare_output(path_text: str, overwrite: bool) -> Path:
    path = Path(path_text).expanduser().resolve()
    if path.exists() and not overwrite:
        raise RuntimeError(f"output exists; use --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_ffmpeg(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return
    message = (proc.stderr or proc.stdout or "").strip()
    if not message:
        message = f"ffmpeg failed with exit code {proc.returncode}"
    raise RuntimeError(message)


def command_frame(parsed: argparse.Namespace) -> int:
    require_ffmpeg()
    input_path = require_input_file(parsed.input)
    output_path = prepare_output(parsed.out, parsed.overwrite)
    if parsed.time and parsed.index is not None:
        raise RuntimeError("--time and --index cannot be used together")

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    cmd.append("-y" if parsed.overwrite else "-n")

    if parsed.index is not None:
        cmd.extend(
            [
                "-i",
                str(input_path),
                "-vf",
                f"select=eq(n\\,{parsed.index})",
                "-vframes",
                "1",
                str(output_path),
            ]
        )
    elif parsed.time:
        cmd.extend(
            [
                "-ss",
                parsed.time,
                "-i",
                str(input_path),
                "-frames:v",
                "1",
                str(output_path),
            ]
        )
    else:
        cmd.extend(
            [
                "-i",
                str(input_path),
                "-vf",
                "select=eq(n\\,0)",
                "-vframes",
                "1",
                str(output_path),
            ]
        )

    run_ffmpeg(cmd)
    print(str(output_path))
    return 0


def command_clip(parsed: argparse.Namespace) -> int:
    require_ffmpeg()
    input_path = require_input_file(parsed.input)
    output_path = prepare_output(parsed.out, parsed.overwrite)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if parsed.overwrite else "-n",
        "-ss",
        parsed.start,
        "-i",
        str(input_path),
        "-t",
        str(parsed.duration),
        str(output_path),
    ]
    run_ffmpeg(cmd)
    print(str(output_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Frame and clip extraction helper")
    sub = parser.add_subparsers(dest="command", required=True)

    frame = sub.add_parser("frame", help="Extract a single frame")
    frame.add_argument("--input", required=True, help="Input video path")
    frame.add_argument("--out", required=True, help="Output image path")
    frame.add_argument("--time", default="", help="Timestamp, for example 00:00:12")
    frame.add_argument("--index", type=int, default=None, help="Frame index (0-based)")
    frame.add_argument("--overwrite", action="store_true", help="Overwrite output path")
    frame.set_defaults(fn=command_frame)

    clip = sub.add_parser("clip", help="Extract a short clip")
    clip.add_argument("--input", required=True, help="Input video path")
    clip.add_argument("--out", required=True, help="Output clip path")
    clip.add_argument("--start", default="00:00:00", help="Clip start timestamp")
    clip.add_argument("--duration", type=float, required=True, help="Clip duration in seconds")
    clip.add_argument("--overwrite", action="store_true", help="Overwrite output path")
    clip.set_defaults(fn=command_clip)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "frame" and args.index is not None and args.index < 0:
            raise RuntimeError("--index must be >= 0")
        if args.command == "clip" and args.duration <= 0:
            raise RuntimeError("--duration must be > 0")
        return int(args.fn(args))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
