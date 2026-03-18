#!/usr/bin/env python3
"""Build a simple contact sheet from local media candidates."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a contact sheet for candidate stills")
    parser.add_argument("source_dir", type=Path, help="Folder containing image candidates")
    parser.add_argument("output", type=Path, help="Output image path")
    parser.add_argument("--limit", type=int, default=12, help="Max images to include")
    parser.add_argument("--cols", type=int, default=3, help="Columns in the sheet")
    parser.add_argument("--thumb-width", type=int, default=240, help="Thumbnail width")
    parser.add_argument("--thumb-height", type=int, default=360, help="Thumbnail height")
    return parser.parse_args()


def image_candidates(folder: Path) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def main() -> int:
    args = parse_args()
    files = image_candidates(args.source_dir)[: max(args.limit, 1)]
    if not files:
        raise SystemExit(f"No image candidates found in {args.source_dir}")

    rows = (len(files) + args.cols - 1) // args.cols
    label_h = 28
    sheet = Image.new("RGB", (args.cols * args.thumb_width, rows * (args.thumb_height + label_h)), (18, 22, 28))

    for index, path in enumerate(files):
        with Image.open(path) as image:
            thumb = ImageOps.contain(image.convert("RGB"), (args.thumb_width, args.thumb_height))
        canvas = Image.new("RGB", (args.thumb_width, args.thumb_height), (10, 12, 16))
        offset_x = (args.thumb_width - thumb.width) // 2
        offset_y = (args.thumb_height - thumb.height) // 2
        canvas.paste(thumb, (offset_x, offset_y))

        x = (index % args.cols) * args.thumb_width
        y = (index // args.cols) * (args.thumb_height + label_h)
        sheet.paste(canvas, (x, y))
        draw = ImageDraw.Draw(sheet)
        draw.text((x + 6, y + args.thumb_height + 6), path.name, fill=(220, 230, 240))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=90)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
