#!/usr/bin/env python3
"""Build a loop-oriented VFI master through ComfyUI using RIFE or FILM."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from local_defaults import DEFAULT_COMFY_OUTPUT, default_filename_prefix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a loop-oriented VFI master in ComfyUI")
    parser.add_argument("input", type=Path, help="Input raw video")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Comfy base URL")
    parser.add_argument("--method", choices=["rife", "film"], default="rife", help="VFI engine")
    parser.add_argument("--target-fps", type=int, default=30, help="Output fps")
    parser.add_argument("--multiplier", type=int, default=2, help="Interpolation multiplier")
    parser.add_argument("--scale-width", type=int, default=0, help="Optional mastered width")
    parser.add_argument("--scale-height", type=int, default=0, help="Optional mastered height")
    parser.add_argument("--filename-prefix", default=default_filename_prefix("wan_vfi_master"), help="Comfy filename prefix")
    parser.add_argument("--out-dir", type=Path, required=True, help="Evidence/output folder")
    parser.add_argument("--run-name", default="wan_vfi_master", help="Base filename for artifacts")
    parser.add_argument("--clear-cache-after-n-frames", type=int, default=10, help="VFI cache clear cadence")
    parser.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default="float16", help="RIFE dtype")
    parser.add_argument("--batch-size", type=int, default=1, help="RIFE batch size")
    parser.add_argument("--loop-mode", choices=["pingpong", "none"], default="none", help="Whether to ping-pong the source before interpolation")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval")
    parser.add_argument("--max-seconds", type=int, default=1800, help="Max time to wait")
    parser.add_argument("--server-loss-threshold", type=int, default=6, help="Consecutive connection failures before aborting")
    return parser.parse_args()


def http_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def ffprobe_stream(video: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,nb_frames",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    width = int(stream["width"])
    height = int(stream["height"])
    rate = stream.get("avg_frame_rate", "0/1")
    try:
        num, den = rate.split("/", 1)
        fps = float(num) / float(den)
    except Exception:
        fps = 0.0
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "nb_frames": int(stream.get("nb_frames") or 0),
    }


def build_pingpong_loop(source: Path, temp_dir: Path) -> Path:
    reverse_source = temp_dir / "reverse_source.mp4"
    reverse_clip = temp_dir / "reverse_trimmed.mp4"
    raw_loop = temp_dir / "loop_source.mp4"
    meta = ffprobe_stream(source)
    frame_count = max(int(meta["nb_frames"]), 0)
    if frame_count < 3:
        return source

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(source), "-vf", "reverse", "-an", str(reverse_source)],
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
            str(reverse_clip),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    concat_list = temp_dir / "concat.txt"
    concat_list.write_text(
        "file '{a}'\nfile '{b}'\n".format(
            a=str(source).replace("'", "'\\''"),
            b=str(reverse_clip).replace("'", "'\\''"),
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(raw_loop)],
        check=True,
        capture_output=True,
        text=True,
    )
    return raw_loop


def extract_frames(source: Path, frames_dir: Path) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(source), "-vsync", "0", str(frames_dir / "frame_%06d.png")],
        check=True,
        capture_output=True,
        text=True,
    )


def build_prompt(args: argparse.Namespace, frames_dir: Path, width: int, height: int) -> dict[str, dict]:
    if args.method == "rife":
        vfi_node = {
            "class_type": "RIFE VFI",
            "inputs": {
                "ckpt_name": "rife49.pth",
                "frames": ["10", 0],
                "clear_cache_after_n_frames": args.clear_cache_after_n_frames,
                "multiplier": args.multiplier,
                "fast_mode": True,
                "ensemble": False,
                "scale_factor": 1.0,
                "dtype": args.dtype,
                "torch_compile": False,
                "batch_size": args.batch_size,
            },
        }
    else:
        vfi_node = {
            "class_type": "FILM VFI",
            "inputs": {
                "ckpt_name": "film_net_fp32.pt",
                "frames": ["10", 0],
                "clear_cache_after_n_frames": args.clear_cache_after_n_frames,
                "multiplier": max(args.multiplier, 2),
            },
        }

    return {
        "10": {
            "class_type": "LoadImagesFromFolderKJ",
            "inputs": {
                "folder": str(frames_dir),
                "width": width,
                "height": height,
                "keep_aspect_ratio": "stretch",
                "image_load_cap": 0,
                "start_index": 0,
                "include_subfolders": False,
            },
        },
        "20": vfi_node,
        "30": {
            "class_type": "CreateVideo",
            "inputs": {
                "images": ["20", 0],
                "fps": float(args.target_fps),
            },
        },
        "9999": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["30", 0],
                "filename_prefix": args.filename_prefix,
                "format": "mp4",
                "codec": "h264",
            },
        },
    }


def scale_video(source: Path, output: Path, width: int, height: int) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vf",
            f"scale={width}:{height}:flags=lanczos,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = args.out_dir / f"{args.run_name}.prompt.json"
    result_path = args.out_dir / f"{args.run_name}.result.json"
    error_path = args.out_dir / f"{args.run_name}.error.json"

    with tempfile.TemporaryDirectory(prefix="wan-loop-vfi-") as tmpdir:
        temp_dir = Path(tmpdir)
        loop_source = args.input
        if args.loop_mode == "pingpong":
            loop_source = build_pingpong_loop(args.input, temp_dir)

        frames_dir = temp_dir / "frames"
        extract_frames(loop_source, frames_dir)
        meta = ffprobe_stream(loop_source)
        width = int(meta["width"])
        height = int(meta["height"])

        prompt = build_prompt(args, frames_dir, width, height)
        prompt_path.write_text(json.dumps(prompt, indent=2), encoding="utf-8")

        request = Request(
            f"{args.base_url}/prompt",
            data=json.dumps({"prompt": prompt}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                submit = json.load(response)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            error_path.write_text(json.dumps({"http_error": exc.code, "body": body}, indent=2), encoding="utf-8")
            return 1
        except Exception as exc:
            error_path.write_text(json.dumps({"error": str(exc)}, indent=2), encoding="utf-8")
            return 1

        prompt_id = submit["prompt_id"]
        deadline = time.time() + max(args.max_seconds, 1)
        lost_server_count = 0
        history = None
        status = "submitted"

        while time.time() < deadline:
            try:
                history_payload = http_json(f"{args.base_url}/history/{prompt_id}")
                lost_server_count = 0
            except (URLError, TimeoutError, ConnectionError) as exc:
                lost_server_count += 1
                if lost_server_count >= args.server_loss_threshold:
                    payload = {"prompt_id": prompt_id, "submit": submit, "status": "server_lost", "error": str(exc)}
                    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    return 1
                time.sleep(args.poll_seconds)
                continue
            except Exception as exc:
                payload = {"prompt_id": prompt_id, "submit": submit, "status": "history_error", "error": str(exc)}
                result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return 1

            if prompt_id in history_payload:
                history = history_payload[prompt_id]
                outputs = history.get("outputs", {})
                if outputs:
                    status = "completed"
                    break
                status_str = history.get("status", {}).get("status_str")
                if status_str in {"error", "failed"}:
                    status = status_str
                    break
            time.sleep(args.poll_seconds)

        payload = {"prompt_id": prompt_id, "submit": submit, "status": status, "history_found": history is not None, "history": history}
        result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if status != "completed" or not history:
            return 1

        video_record = None
        for node_output in history.get("outputs", {}).values():
            videos = node_output.get("videos")
            if videos:
                video_record = videos[0]
                break
            images = node_output.get("images")
            animated = node_output.get("animated") or []
            if images:
                first_image = images[0]
                if str(first_image.get("filename", "")).lower().endswith(".mp4") or any(animated):
                    video_record = first_image
                    break
        if not video_record:
            error_path.write_text(json.dumps({"error": "no_video_output_record_found", "prompt_id": prompt_id}, indent=2), encoding="utf-8")
            return 1

        source_video = DEFAULT_COMFY_OUTPUT / video_record["subfolder"] / video_record["filename"]
        raw_target = args.out_dir / video_record["filename"]
        shutil.copy2(source_video, raw_target)

        final_target = raw_target
        if args.scale_width > 0 and args.scale_height > 0:
            final_target = args.out_dir / f"{Path(video_record['filename']).stem}_scaled.mp4"
            scale_video(raw_target, final_target, args.scale_width, args.scale_height)

        print(final_target)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
