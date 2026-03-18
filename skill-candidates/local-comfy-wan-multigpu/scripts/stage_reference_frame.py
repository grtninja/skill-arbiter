#!/usr/bin/env python3
"""Stage a reference frame without destructive center-crop by default."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage a source still for local video generation")
    parser.add_argument("source", type=Path, help="Source image path")
    parser.add_argument("output", type=Path, help="Output staged image path")
    parser.add_argument("--width", type=int, default=1280, help="Target width")
    parser.add_argument("--height", type=int, default=720, help="Target height")
    parser.add_argument(
        "--mode",
        choices=("fit", "pad", "crop"),
        default="pad",
        help="fit keeps the full image, pad letterboxes, crop is opt-in only",
    )
    parser.add_argument("--background", default="10,12,16", help="RGB background for pad mode, e.g. 10,12,16")
    return parser.parse_args()


def parse_background(value: str) -> tuple[int, int, int]:
    parts = [int(item.strip()) for item in value.split(",")]
    if len(parts) != 3:
        raise ValueError("Background must be three comma-separated integers")
    return tuple(parts)  # type: ignore[return-value]


def main() -> int:
    args = parse_args()
    background = parse_background(args.background)

    with Image.open(args.source) as image:
        image = image.convert("RGB")
        if args.mode == "crop":
            scale = max(args.width / image.width, args.height / image.height)
            resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
            left = max((resized.width - args.width) // 2, 0)
            top = max((resized.height - args.height) // 2, 0)
            staged = resized.crop((left, top, left + args.width, top + args.height))
        else:
            scale = min(args.width / image.width, args.height / image.height)
            resized = image.resize((max(round(image.width * scale), 1), max(round(image.height * scale), 1)), Image.Resampling.LANCZOS)
            if args.mode == "fit":
                staged = resized
            else:
                staged = Image.new("RGB", (args.width, args.height), background)
                x = (args.width - resized.width) // 2
                y = (args.height - resized.height) // 2
                staged.paste(resized, (x, y))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    staged.save(args.output, quality=95)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
