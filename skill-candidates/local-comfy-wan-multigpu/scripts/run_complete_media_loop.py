#!/usr/bin/env python3
"""Run a complete local Penny media loop from approved stills or keyframes."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from local_defaults import (
    DEFAULT_COMFY_INPUT,
    DEFAULT_KOKORO_MODEL,
    DEFAULT_KOKORO_VOICES,
    DEFAULT_MUSETALK_REPO,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a complete local Penny media loop")
    parser.add_argument("sources", nargs="+", type=Path, help="One approved still or an ordered range of approved keyframes")
    parser.add_argument("--job-name", required=True, help="Short work item name")
    parser.add_argument("--subject", default="Penny", help="Subject name")
    parser.add_argument("--continuity-profile", default="penny_canon_v1", help="Continuity profile id")
    parser.add_argument("--notes", default="", help="Operator notes")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010", help="Dedicated Comfy base URL")
    parser.add_argument("--width", type=int, default=640, help="Target width")
    parser.add_argument("--height", type=int, default=992, help="Target height")
    parser.add_argument("--stage-mode", choices=("pad", "fit", "crop"), default="pad", help="Reference staging mode")
    parser.add_argument("--length", type=int, default=81, help="Wan latent length per segment")
    parser.add_argument("--fps", type=float, default=16.0, help="Wan raw fps")
    parser.add_argument("--quality-preset", choices=("quality", "fast"), default="quality", help="Wan quality preset")
    parser.add_argument("--seed", type=int, default=984937593540091, help="Wan noise seed")
    parser.add_argument("--positive", required=True, help="Positive prompt")
    parser.add_argument("--negative", default="", help="Negative prompt override")
    parser.add_argument("--clip-device", default="cpu", help="MultiGPU CLIP device")
    parser.add_argument("--vae-device", default="cuda:0", help="MultiGPU VAE device")
    parser.add_argument("--high-noise-device", default="cuda:1", help="MultiGPU high-noise UNet device")
    parser.add_argument("--low-noise-device", default="cuda:0", help="MultiGPU low-noise UNet device")
    parser.add_argument("--speech-text", default="", help="Optional dialogue line")
    parser.add_argument("--voice", default="af_jessica", help="Kokoro voice id")
    parser.add_argument("--tts-lang", default="en-US", help="Kokoro language tag")
    parser.add_argument("--tts-speed", type=float, default=0.92, help="Kokoro speech speed")
    parser.add_argument("--tts-pitch-shift", type=float, default=0.0, help="Post-synthesis pitch shift in semitones")
    parser.add_argument("--kokoro-model", type=Path, default=DEFAULT_KOKORO_MODEL, help="Path to kokoro-v1.0.onnx")
    parser.add_argument("--kokoro-voices", type=Path, default=DEFAULT_KOKORO_VOICES, help="Path to voices-v1.0.bin")
    parser.add_argument("--musetalk-repo", type=Path, default=DEFAULT_MUSETALK_REPO, help="MuseTalk repo root")
    parser.add_argument("--musetalk-python", type=Path, help="MuseTalk python interpreter")
    parser.add_argument("--musetalk-cuda-visible-devices", default="1", help="CUDA_VISIBLE_DEVICES for MuseTalk")
    parser.add_argument("--musetalk-gpu-id", type=int, default=0, help="MuseTalk gpu_id after masking")
    parser.add_argument(
        "--export-fps",
        type=int,
        nargs="*",
        default=[25, 30, 60],
        help="Export fps set for spoken masters; 25 means native copy",
    )
    parser.add_argument("--open-explorer", action="store_true", help="Open the final folder in Explorer")
    return parser.parse_args()


def script_path(name: str) -> Path:
    return Path(__file__).with_name(name)


def slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def run_checked(cmd: list[str], workdir: Path | None = None) -> str:
    completed = subprocess.run(
        cmd,
        cwd=str(workdir) if workdir else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    stdout = (completed.stdout or "").strip()
    return stdout.splitlines()[-1].strip() if stdout else ""


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def stage_sources(args: argparse.Namespace, job_dir: Path) -> list[Path]:
    staged_dir = job_dir / "01_staged"
    comfy_input = DEFAULT_COMFY_INPUT
    stage_script = script_path("stage_reference_frame.py")
    staged_paths: list[Path] = []
    for index, source in enumerate(args.sources, start=1):
        if not source.exists():
            raise SystemExit(f"Missing source: {source}")
        staged_name = f"keyframe_{index:02d}_{slugify(source.stem)}_{args.width}x{args.height}.jpg"
        staged_path = staged_dir / staged_name
        run_checked(
            [
                "python",
                str(stage_script),
                str(source),
                str(staged_path),
                "--width",
                str(args.width),
                "--height",
                str(args.height),
                "--mode",
                args.stage_mode,
            ]
        )
        shutil.copy2(staged_path, comfy_input / staged_path.name)
        staged_paths.append(staged_path)
    return staged_paths


def export_interpolated(source_video: Path, target_video: Path, fps: int) -> None:
    target_video.parent.mkdir(parents=True, exist_ok=True)
    if fps == 25:
        shutil.copy2(source_video, target_video)
        return
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_video),
            "-vf",
            f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-c:a",
            "copy",
            str(target_video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> int:
    args = parse_args()
    init_script = script_path("init_media_job.py")
    review_script = script_path("review_video_result.py")
    keyframe_runner = script_path("run_keyframe_range_pipeline.py")
    tts_script = script_path("synthesize_kokoro_tts.py")
    asr_script = script_path("analyze_spoken_clip.py")
    musetalk_script = script_path("run_musetalk_pass.py")

    job_dir = Path(
        run_checked(
            [
                "python",
                str(init_script),
                str(args.sources[0]),
                "--job-name",
                args.job_name,
                "--subject",
                args.subject,
                "--continuity-profile",
                args.continuity_profile,
                "--expected-dialogue",
                args.speech_text,
                "--notes",
                args.notes,
            ]
        )
    )
    manifest_path = job_dir / "10_sidecars" / "job_manifest.json"
    manifest = load_manifest(manifest_path)
    staged_paths = stage_sources(args, job_dir)
    staged_names = [path.name for path in staged_paths]

    raw_dir = job_dir / "02_raw_forward"
    raw_name = f"{manifest['job_slug']}_raw"
    raw_video = Path(
        run_checked(
            [
                "python",
                str(keyframe_runner),
                "--base-url",
                args.base_url,
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
                str(args.seed),
                "--clip-device",
                args.clip_device,
                "--vae-device",
                args.vae_device,
                "--high-noise-device",
                args.high_noise_device,
                "--low-noise-device",
                args.low_noise_device,
                "--out-dir",
                str(raw_dir),
                "--run-name",
                raw_name,
                *staged_names,
            ]
        )
    )

    review_dir = job_dir / "03_review"
    review_sheet = review_dir / f"{raw_video.stem}_review_sheet.jpg"
    run_checked(["python", str(review_script), str(raw_video), str(review_sheet), "--count", "8", "--cols", "4"])
    manifest["status"]["raw_forward_complete"] = True
    manifest["status"]["review_complete"] = True

    exports_dir = job_dir / "09_exports"
    if args.speech_text.strip():
        if not args.kokoro_model.exists() or not args.kokoro_voices.exists():
            raise SystemExit("Kokoro model files are missing for the spoken pass")
        if not args.musetalk_python:
            raise SystemExit("--musetalk-python is required for the spoken pass")

        audio_dir = job_dir / "05_audio_tts"
        audio_base = f"{manifest['job_slug']}_{args.voice}"
        raw_audio = audio_dir / f"{audio_base}.wav"
        audio_meta = audio_dir / f"{audio_base}.json"
        run_checked(
            [
                "python",
                str(tts_script),
                "--model",
                str(args.kokoro_model),
                "--voices",
                str(args.kokoro_voices),
                "--output",
                str(raw_audio),
                "--voice",
                args.voice,
                "--lang",
                args.tts_lang,
                "--speed",
                str(args.tts_speed),
                "--pitch-shift",
                str(args.tts_pitch_shift),
                "--text",
                args.speech_text,
                "--meta-out",
                str(audio_meta),
            ]
        )
        audio_16k = audio_dir / f"{audio_base}_16k.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_audio), "-ac", "1", "-ar", "16000", str(audio_16k)],
            check=True,
            capture_output=True,
            text=True,
        )
        manifest["status"]["tts_complete"] = True

        lipsync_dir = job_dir / "06_lipsync" / f"musetalk_{args.voice}"
        lipsync_name = f"{manifest['job_slug']}_{args.voice}_musetalk"
        spoken_video = Path(
            run_checked(
                [
                    "python",
                    str(musetalk_script),
                    "--repo-root",
                    str(args.musetalk_repo),
                    "--python",
                    str(args.musetalk_python),
                    "--video",
                    str(raw_video),
                    "--audio",
                    str(audio_16k),
                    "--out-dir",
                    str(lipsync_dir),
                    "--run-name",
                    lipsync_name,
                    "--version",
                    "v15",
                    "--cuda-visible-devices",
                    args.musetalk_cuda_visible_devices,
                    "--gpu-id",
                    str(args.musetalk_gpu_id),
                ]
            )
        )
        spoken_review = review_dir / f"{spoken_video.stem}_review_sheet.jpg"
        run_checked(["python", str(review_script), str(spoken_video), str(spoken_review), "--count", "8", "--cols", "4"])
        manifest["status"]["lipsync_complete"] = True

        qc_dir = job_dir / "07_asr_qc"
        qc_name = spoken_video.stem
        run_checked(
            [
                "python",
                str(asr_script),
                str(spoken_video),
                "--out-dir",
                str(qc_dir),
                "--run-name",
                qc_name,
                "--expected-text",
                args.speech_text,
            ]
        )
        manifest["status"]["asr_qc_complete"] = True

        export_base = f"{args.subject.upper()}_{manifest['created_at_local'][:10].replace('-', '')}_{manifest['job_slug']}_{args.voice}_musetalk"
        subtitle_source = qc_dir / f"{qc_name}.transcript.srt"
        if subtitle_source.exists():
            shutil.copy2(subtitle_source, exports_dir / f"{export_base}.srt")
        for fps in sorted(set(args.export_fps)):
            export_interpolated(spoken_video, exports_dir / f"{export_base}_{fps}fps.mp4", fps)
        manifest["status"]["final_export_complete"] = True
    else:
        raw_export = exports_dir / f"{args.subject.upper()}_{manifest['created_at_local'][:10].replace('-', '')}_{manifest['job_slug']}_raw_{int(args.fps)}fps.mp4"
        shutil.copy2(raw_video, raw_export)
        manifest["status"]["final_export_complete"] = True

    save_manifest(manifest_path, manifest)

    if args.open_explorer:
        target_dir = exports_dir if any(exports_dir.iterdir()) else job_dir
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Start-Process explorer.exe '{target_dir}'"], check=False)

    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
