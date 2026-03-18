#!/usr/bin/env python3
"""Run one or more Wan FLF segments and stitch them into a single clip."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from local_defaults import default_filename_prefix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a keyframe-range Wan FLF pipeline")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Comfy base URL")
    parser.add_argument("--width", type=int, default=640, help="Target width")
    parser.add_argument("--height", type=int, default=992, help="Target height")
    parser.add_argument("--length", type=int, default=81, help="Wan latent length per segment")
    parser.add_argument("--fps", type=float, default=16.0, help="Video fps")
    parser.add_argument("--positive", required=True, help="Positive prompt")
    parser.add_argument("--negative", required=True, help="Negative prompt")
    parser.add_argument("--quality-preset", choices=("quality", "fast"), default="quality", help="Sampling preset")
    parser.add_argument("--seed", type=int, default=984937593540091, help="Noise seed")
    parser.add_argument("--clip-device", default="cpu", help="MultiGPU CLIP device")
    parser.add_argument("--vae-device", default="cuda:0", help="MultiGPU VAE device")
    parser.add_argument("--high-noise-device", default="cuda:1", help="MultiGPU high-noise UNet device")
    parser.add_argument("--low-noise-device", default="cuda:0", help="MultiGPU low-noise UNet device")
    parser.add_argument(
        "--disable-multigpu-loaders",
        action="store_true",
        help="Force plain loaders even if MultiGPU nodes are available",
    )
    parser.add_argument("--out-dir", type=Path, required=True, help="Evidence/output folder")
    parser.add_argument("--run-name", default="wan_keyframe_range", help="Base filename")
    parser.add_argument("images", nargs="+", help="One or more LoadImage-visible filenames in order")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    run_flf = Path(__file__).with_name("run_wan_flf2v.py")
    manifest_path = args.out_dir / f"{args.run_name}.segments.json"
    segments_dir = args.out_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    image_sequence = list(args.images)
    if len(image_sequence) == 1:
        image_sequence.append(image_sequence[0])

    segment_videos: list[Path] = []
    segment_metadata: list[dict[str, str | int]] = []
    for index in range(len(image_sequence) - 1):
        start_image = image_sequence[index]
        end_image = image_sequence[index + 1]
        segment_name = f"{args.run_name}_segment_{index + 1:02d}"
        segment_out_dir = segments_dir / segment_name
        segment_out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(run_flf),
            "--base-url",
            args.base_url,
            "--start-image",
            start_image,
            "--end-image",
            end_image,
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--length",
            str(args.length),
            "--fps",
            str(args.fps),
            "--positive",
            args.positive,
            "--negative",
            args.negative,
            "--quality-preset",
            args.quality_preset,
            "--seed",
            str(args.seed + index),
            "--clip-device",
            args.clip_device,
            "--vae-device",
            args.vae_device,
            "--high-noise-device",
            args.high_noise_device,
            "--low-noise-device",
            args.low_noise_device,
            "--filename-prefix",
            default_filename_prefix(segment_name),
            "--out-dir",
            str(segment_out_dir),
            "--run-name",
            segment_name,
        ]
        if args.disable_multigpu_loaders:
            cmd.append("--disable-multigpu-loaders")
        subprocess.run(cmd, check=True)
        outputs = sorted(segment_out_dir.glob("*.mp4"))
        if not outputs:
            raise SystemExit(f"Segment completed without mp4 output: {segment_name}")
        segment_videos.append(outputs[0])
        segment_metadata.append(
            {
                "index": index + 1,
                "start_image": start_image,
                "end_image": end_image,
                "video": str(outputs[0]),
            }
        )

    final_video = args.out_dir / f"{args.run_name}.mp4"
    if len(segment_videos) == 1:
        shutil.copy2(segment_videos[0], final_video)
    else:
        concat_manifest = args.out_dir / f"{args.run_name}.concat.txt"
        concat_manifest.write_text(
            "\n".join([f"file '{path.as_posix()}'" for path in segment_videos]),
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
                str(concat_manifest),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "18",
                str(final_video),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    manifest_path.write_text(
        json.dumps(
            {
                "run_name": args.run_name,
                "images": image_sequence,
                "segment_count": len(segment_metadata),
                "segments": segment_metadata,
                "final_video": str(final_video),
                "quality_preset": args.quality_preset,
                "device_placement": {
                    "clip_device": args.clip_device,
                    "vae_device": args.vae_device,
                    "high_noise_device": args.high_noise_device,
                    "low_noise_device": args.low_noise_device,
                    "disable_multigpu_loaders": args.disable_multigpu_loaders,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(final_video)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
