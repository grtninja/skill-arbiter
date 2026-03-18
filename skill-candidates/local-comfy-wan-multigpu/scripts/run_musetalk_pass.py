#!/usr/bin/env python3
"""Run a MuseTalk pass against an animated source clip and audio."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MuseTalk against an animated source clip")
    parser.add_argument("--repo-root", type=Path, required=True, help="MuseTalk repo root")
    parser.add_argument("--python", type=Path, required=True, help="MuseTalk python interpreter")
    parser.add_argument("--video", type=Path, required=True, help="Animated source video")
    parser.add_argument("--audio", type=Path, required=True, help="Source audio")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory for YAML/log/results")
    parser.add_argument("--run-name", required=True, help="Result base name")
    parser.add_argument("--version", default="v15", help="MuseTalk version")
    parser.add_argument("--cuda-visible-devices", help="Optional CUDA_VISIBLE_DEVICES value for MuseTalk")
    parser.add_argument("--gpu-id", type=int, default=0, help="MuseTalk gpu_id after any device masking")
    parser.add_argument(
        "--video-prep",
        choices=("fps", "minterpolate"),
        default="minterpolate",
        help="How to normalize source video to MuseTalk's 25 fps training cadence",
    )
    return parser.parse_args()


def ffmpeg_bin_dir() -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH")
    return Path(ffmpeg).resolve().parent


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    normalized_video = args.out_dir / f"{args.run_name}_input_25fps.mp4"
    normalized_audio = args.out_dir / f"{args.run_name}_audio_16k.wav"
    yaml_path = args.out_dir / f"{args.run_name}.yaml"
    log_path = args.out_dir / f"{args.run_name}.log"
    sidecar_path = args.out_dir / f"{args.run_name}.musetalk.json"

    if args.video_prep == "minterpolate":
        video_filter = "minterpolate=fps=25:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    else:
        video_filter = "fps=25"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(args.video),
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            str(normalized_video),
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
            str(args.audio),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(normalized_audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    yaml_path.write_text(
        "\n".join(
            [
                "task_0:",
                f'  video_path: "{normalized_video.as_posix()}"',
                f'  audio_path: "{normalized_audio.as_posix()}"',
                f'  result_name: "{args.run_name}.mp4"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    cmd = [
        str(args.python),
        "-m",
        "scripts.inference",
        "--inference_config",
        str(yaml_path),
        "--result_dir",
        str(args.out_dir),
        "--unet_model_path",
        "models/musetalkV15/unet.pth",
        "--unet_config",
        "models/musetalkV15/musetalk.json",
        "--version",
        args.version,
        "--gpu_id",
        str(args.gpu_id),
        "--ffmpeg_path",
        str(ffmpeg_bin_dir()),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if args.cuda_visible_devices:
        env["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices
    completed = subprocess.run(
        cmd,
        cwd=str(args.repo_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    combined_log = (completed.stdout or "") + "\n" + (completed.stderr or "")
    log_path.write_text(combined_log, encoding="utf-8")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    result_video = args.out_dir / args.version / f"{args.run_name}.mp4"
    if not result_video.exists():
        raise SystemExit(f"MuseTalk did not produce expected result: {result_video}")

    warnings: list[str] = []
    if "FATAL:" in combined_log:
        warnings.append("runtime_reported_fatal_kernel_messages")
    if "bbox_shift parameter adjustment" in combined_log:
        warnings.append("musetalk_bbox_shift_manual_tuning_available")

    sidecar_path.write_text(
        json.dumps(
            {
                "run_name": args.run_name,
                "normalized_video": str(normalized_video),
                "normalized_audio": str(normalized_audio),
                "yaml_path": str(yaml_path),
                "result_video": str(result_video),
                "log_path": str(log_path),
                "version": args.version,
                "video_prep": args.video_prep,
                "video_filter": video_filter,
                "warnings": warnings,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(result_video)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
