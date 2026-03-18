#!/usr/bin/env python3
"""Extract representative frames from a video and assemble a review sheet."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review sheet from a rendered video")
    parser.add_argument("video", type=Path, help="Rendered video path")
    parser.add_argument("output", type=Path, help="Output review sheet image")
    parser.add_argument("--count", type=int, default=6, help="Number of frames to sample")
    parser.add_argument("--cols", type=int, default=3, help="Columns in the review sheet")
    parser.add_argument("--thumb-width", type=int, default=320, help="Thumb width")
    parser.add_argument("--thumb-height", type=int, default=180, help="Thumb height")
    return parser.parse_args()


def ffprobe_json(video: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=width,height,r_frame_rate",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def extract_frame(video: Path, timestamp: float, output: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    args = parse_args()
    probe = ffprobe_json(args.video)
    duration = float(probe.get("format", {}).get("duration", "0") or "0")
    if duration <= 0:
        raise SystemExit("Video duration is zero or missing")

    count = max(args.count, 2)
    timestamps = [duration * (index + 1) / (count + 1) for index in range(count)]

    with tempfile.TemporaryDirectory(prefix="review-video-") as tmpdir:
        temp_dir = Path(tmpdir)
        frame_paths: list[Path] = []
        for index, timestamp in enumerate(timestamps, start=1):
            frame_path = temp_dir / f"frame_{index:02d}.jpg"
            extract_frame(args.video, timestamp, frame_path)
            frame_paths.append(frame_path)

        rows = math.ceil(len(frame_paths) / args.cols)
        label_h = 24
        sheet = Image.new(
            "RGB",
            (args.cols * args.thumb_width, rows * (args.thumb_height + label_h)),
            (18, 22, 28),
        )

        for index, frame_path in enumerate(frame_paths):
            with Image.open(frame_path) as image:
                image = image.convert("RGB")
                image.thumbnail((args.thumb_width, args.thumb_height))
                canvas = Image.new("RGB", (args.thumb_width, args.thumb_height), (10, 12, 16))
                x = (args.thumb_width - image.width) // 2
                y = (args.thumb_height - image.height) // 2
                canvas.paste(image, (x, y))
            left = (index % args.cols) * args.thumb_width
            top = (index // args.cols) * (args.thumb_height + label_h)
            sheet.paste(canvas, (left, top))
            draw = ImageDraw.Draw(sheet)
            draw.text((left + 6, top + args.thumb_height + 4), f"t={timestamps[index]:.2f}s", fill=(220, 230, 240))

        args.output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.output, quality=92)
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
