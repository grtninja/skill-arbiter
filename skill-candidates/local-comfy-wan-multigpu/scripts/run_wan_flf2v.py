#!/usr/bin/env python3
"""Run a local Wan first/last-frame video render."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from local_defaults import DEFAULT_COMFY_OUTPUT, default_filename_prefix


DEFAULT_NEGATIVE = (
    "overexposed, static frame, bad detail, blurry face, deformed face, distorted anatomy, "
    "extra fingers, malformed hands, warped earrings, background crowd, text, subtitle, "
    "worst quality, low quality, jpeg artifacts, open mouth, talking mouth, teeth, speech pose"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Wan first/last-frame to video")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Comfy base URL")
    parser.add_argument("--start-image", required=True, help="Start image filename visible to LoadImage")
    parser.add_argument("--end-image", help="End image filename visible to LoadImage; defaults to start image")
    parser.add_argument("--width", type=int, default=640, help="Target width")
    parser.add_argument("--height", type=int, default=992, help="Target height")
    parser.add_argument("--length", type=int, default=81, help="Wan latent length")
    parser.add_argument("--fps", type=float, default=16.0, help="Video fps")
    parser.add_argument("--positive", required=True, help="Positive prompt")
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE, help="Negative prompt")
    parser.add_argument("--quality-preset", choices=("quality", "fast"), default="quality", help="Sampling preset")
    parser.add_argument("--seed", type=int, default=984937593540091, help="Noise seed")
    parser.add_argument("--filename-prefix", default=default_filename_prefix("flf_render"), help="Comfy filename prefix")
    parser.add_argument("--out-dir", type=Path, required=True, help="Evidence/output folder")
    parser.add_argument("--run-name", default="wan_flf_render", help="Base filename for JSON artifacts")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval")
    parser.add_argument("--max-seconds", type=int, default=2400, help="Max time to wait")
    parser.add_argument("--server-loss-threshold", type=int, default=6, help="Consecutive connection failures before aborting")
    parser.add_argument(
        "--disable-multigpu-loaders",
        action="store_true",
        help="Force plain Comfy loaders even when MultiGPU loader nodes are available",
    )
    parser.add_argument("--clip-device", default="cpu", help="CLIP device when MultiGPU loaders are available")
    parser.add_argument("--vae-device", default="cuda:0", help="VAE device when MultiGPU loaders are available")
    parser.add_argument("--high-noise-device", default="cuda:1", help="High-noise UNet device when MultiGPU loaders are available")
    parser.add_argument("--low-noise-device", default="cuda:0", help="Low-noise UNet device when MultiGPU loaders are available")
    return parser.parse_args()


def http_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def multigpu_loader_available(base_url: str) -> bool:
    try:
        for node_name in ("UNETLoaderMultiGPU", "CLIPLoaderMultiGPU", "VAELoaderMultiGPU"):
            payload = http_json(f"{base_url}/object_info/{node_name}")
            if node_name not in payload:
                return False
        return True
    except Exception:
        return False


def build_prompt(args: argparse.Namespace, use_multigpu: bool) -> dict[str, dict]:
    end_image = args.end_image or args.start_image
    if use_multigpu:
        clip_loader = {
            "class_type": "CLIPLoaderMultiGPU",
            "inputs": {
                "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "type": "wan",
                "device": args.clip_device,
            },
        }
        unet_high = {
            "class_type": "UNETLoaderMultiGPU",
            "inputs": {
                "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default",
                "device": args.high_noise_device,
            },
        }
        unet_low = {
            "class_type": "UNETLoaderMultiGPU",
            "inputs": {
                "unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                "weight_dtype": "default",
                "device": args.low_noise_device,
            },
        }
        vae_loader = {
            "class_type": "VAELoaderMultiGPU",
            "inputs": {"vae_name": "wan_2.1_vae.safetensors", "device": args.vae_device},
        }
    else:
        clip_loader = {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"},
        }
        unet_high = {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"},
        }
        unet_low = {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"},
        }
        vae_loader = {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}}
    if args.quality_preset == "quality":
        high_model_ref = ["104", 0]
        low_model_ref = ["103", 0]
        shift = 8.0
        sampler_steps = 20
        sampler_cfg = 4.0
        split_step = 10
        high_model_node = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["95", 0], "shift": shift}}
        low_model_node = {"class_type": "ModelSamplingSD3", "inputs": {"model": ["96", 0], "shift": shift}}
    else:
        high_model_ref = ["104", 0]
        low_model_ref = ["103", 0]
        shift = 5.0
        sampler_steps = 4
        sampler_cfg = 1.0
        split_step = 2
        high_model_node = {
            "class_type": "ModelSamplingSD3",
            "inputs": {"model": ["101", 0], "shift": shift},
        }
        low_model_node = {
            "class_type": "ModelSamplingSD3",
            "inputs": {"model": ["102", 0], "shift": shift},
        }

    prompt: dict[str, dict] = {
        "9000": {"class_type": "LoadImage", "inputs": {"image": args.start_image}},
        "9001": {"class_type": "LoadImage", "inputs": {"image": end_image}},
        "84": clip_loader,
        "90": vae_loader,
        "95": unet_high,
        "96": unet_low,
        "93": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["84", 0], "text": args.positive}},
        "89": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["84", 0], "text": args.negative}},
        "98": {
            "class_type": "WanFirstLastFrameToVideo",
            "inputs": {
                "positive": ["93", 0],
                "negative": ["89", 0],
                "vae": ["90", 0],
                "start_image": ["9000", 0],
                "end_image": ["9001", 0],
                "width": args.width,
                "height": args.height,
                "length": args.length,
                "batch_size": 1,
            },
        },
        "104": high_model_node,
        "103": low_model_node,
        "86": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "model": high_model_ref,
                "positive": ["98", 0],
                "negative": ["98", 1],
                "latent_image": ["98", 2],
                "add_noise": "enable",
                "noise_seed": args.seed,
                "steps": sampler_steps,
                "cfg": sampler_cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": 0,
                "end_at_step": split_step,
                "return_with_leftover_noise": "enable",
            },
        },
        "85": {
            "class_type": "KSamplerAdvanced",
            "inputs": {
                "model": low_model_ref,
                "positive": ["98", 0],
                "negative": ["98", 1],
                "latent_image": ["86", 0],
                "add_noise": "disable",
                "noise_seed": args.seed,
                "steps": sampler_steps,
                "cfg": sampler_cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "start_at_step": split_step,
                "end_at_step": 10000 if args.quality_preset == "quality" else sampler_steps,
                "return_with_leftover_noise": "disable",
            },
        },
        "87": {"class_type": "VAEDecode", "inputs": {"samples": ["85", 0], "vae": ["90", 0]}},
        "117": {"class_type": "CreateVideo", "inputs": {"images": ["87", 0], "fps": args.fps}},
        "9999": {"class_type": "SaveVideo", "inputs": {"video": ["117", 0], "filename_prefix": args.filename_prefix, "format": "mp4", "codec": "h264"}},
    }
    if args.quality_preset == "fast":
        prompt["101"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["95", 0],
                "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
                "strength_model": 1.0,
            },
        }
        prompt["102"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["96", 0],
                "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
                "strength_model": 1.0,
            },
        }
    return prompt


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = args.out_dir / f"{args.run_name}.prompt.json"
    result_path = args.out_dir / f"{args.run_name}.result.json"
    error_path = args.out_dir / f"{args.run_name}.error.json"

    load_image_info = http_json(f"{args.base_url}/object_info/LoadImage")
    options = load_image_info.get("LoadImage", {}).get("input", {}).get("required", {}).get("image", [[]])[0]
    end_image = args.end_image or args.start_image
    for image_name in (args.start_image, end_image):
        if image_name not in options:
            error_path.write_text(
                json.dumps({"error": "input_image_not_visible_to_loadimage", "input_image": image_name}, indent=2),
                encoding="utf-8",
            )
            return 1

    use_multigpu = False
    if not args.disable_multigpu_loaders:
        use_multigpu = multigpu_loader_available(args.base_url)

    prompt = build_prompt(args, use_multigpu)
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

    payload = {
        "prompt_id": prompt_id,
        "submit": submit,
        "status": status,
        "history_found": history is not None,
        "history": history,
        "quality_preset": args.quality_preset,
        "start_image": args.start_image,
        "end_image": end_image,
        "use_multigpu_loaders": use_multigpu,
        "device_placement": {
            "clip_device": args.clip_device if use_multigpu else "default",
            "vae_device": args.vae_device if use_multigpu else "default",
            "high_noise_device": args.high_noise_device if use_multigpu else "default",
            "low_noise_device": args.low_noise_device if use_multigpu else "default",
        },
    }
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
    target_video = args.out_dir / video_record["filename"]
    shutil.copy2(source_video, target_video)
    print(target_video)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
