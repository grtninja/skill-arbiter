#!/usr/bin/env python3
"""Run a quality-first recursive Penny refinement batch."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from local_defaults import (
    DEFAULT_COMFY_BASE,
    DEFAULT_COMFY_DB_URL,
    DEFAULT_COMFY_EXTRA_MODELS,
    DEFAULT_COMFY_FRONTEND,
    DEFAULT_COMFY_INPUT,
    DEFAULT_COMFY_MAIN,
    DEFAULT_COMFY_OUTPUT,
    DEFAULT_COMFY_PYTHON,
    DEFAULT_COMFY_USER,
    DEFAULT_KOKORO_MODEL,
    DEFAULT_KOKORO_VOICES,
    DEFAULT_MUSETALK_REPO,
    DEFAULT_WORKBENCH_TOOLS,
    DEFAULT_WORK_ITEMS,
    default_filename_prefix,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a recursive Penny refinement batch")
    parser.add_argument("source", type=Path, help="Approved source still")
    parser.add_argument("--job-name", required=True, help="Batch job name")
    parser.add_argument("--root", type=Path, default=DEFAULT_WORK_ITEMS, help="Workbench work-items root")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010", help="Dedicated Comfy base URL")
    parser.add_argument("--width", type=int, default=720, help="Target staged/render width")
    parser.add_argument("--height", type=int, default=1280, help="Target staged/render height")
    parser.add_argument("--stage-mode", choices=("pad", "fit", "crop"), default="pad", help="Stage mode")
    parser.add_argument("--length", type=int, default=129, help="Wan latent length for each raw render")
    parser.add_argument("--fps", type=float, default=16.0, help="Native Wan fps")
    parser.add_argument("--speech-text", required=True, help="Dialogue line for the spoken batch")
    parser.add_argument("--voice", default="af_jessica", help="Kokoro voice id")
    parser.add_argument("--tts-lang", default="en-US", help="Kokoro language")
    parser.add_argument("--tts-speed", type=float, default=0.92, help="Kokoro speed")
    parser.add_argument("--tts-pitch-shift", type=float, default=0.0, help="Kokoro pitch shift")
    parser.add_argument("--kokoro-model", type=Path, default=DEFAULT_KOKORO_MODEL, help="kokoro-v1.0.onnx")
    parser.add_argument("--kokoro-voices", type=Path, default=DEFAULT_KOKORO_VOICES, help="voices-v1.0.bin")
    parser.add_argument("--musetalk-repo", type=Path, default=DEFAULT_MUSETALK_REPO, help="MuseTalk repo root")
    parser.add_argument("--musetalk-python", type=Path, required=True, help="MuseTalk python interpreter")
    parser.add_argument("--musetalk-cuda-visible-devices", default="1", help="CUDA_VISIBLE_DEVICES mask for MuseTalk")
    parser.add_argument("--musetalk-gpu-id", type=int, default=0, help="MuseTalk gpu_id after masking")
    parser.add_argument(
        "--musetalk-video-prep",
        choices=("fps", "minterpolate"),
        default="minterpolate",
        help="How to normalize animated source clips to MuseTalk's 25 fps cadence",
    )
    parser.add_argument("--max-profiles", type=int, default=2, help="How many motion profiles to carry through the full spoken batch")
    parser.add_argument("--raw-timeout-seconds", type=int, default=4200, help="Hard timeout for each raw Wan render")
    parser.add_argument("--musetalk-timeout-seconds", type=int, default=2400, help="Hard timeout for each MuseTalk pass")
    parser.add_argument("--vfi-timeout-seconds", type=int, default=2400, help="Hard timeout for each VFI master pass")
    parser.add_argument("--parallel-followups", type=int, default=2, help="How many follow-up profile pipelines may run at once")
    parser.add_argument("--open-explorer", action="store_true", help="Open the final export folder")
    return parser.parse_args()


def script_path(name: str) -> Path:
    return Path(__file__).with_name(name)


def slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def run_checked(
    cmd: list[str],
    workdir: Path | None = None,
    *,
    timeout_s: int | None = None,
    env: dict[str, str] | None = None,
) -> str:
    completed = subprocess.run(
        cmd,
        cwd=str(workdir) if workdir else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=timeout_s,
    )
    stdout = (completed.stdout or "").strip()
    return stdout.splitlines()[-1].strip() if stdout else ""


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def run_vfi_master(
    source_video: Path,
    target_video: Path,
    *,
    base_url: str,
    out_dir: Path,
    run_name: str,
    fps: int,
    timeout_s: int,
) -> None:
    if fps == 25:
        shutil.copy2(source_video, target_video)
        return
    vfi_script = script_path("run_loop_vfi_master.py")
    temp_out_dir = out_dir / "_vfi"
    temp_out_dir.mkdir(parents=True, exist_ok=True)
    result_path = Path(
        run_checked(
            [
                "python",
                str(vfi_script),
                str(source_video),
                "--base-url",
                base_url,
                "--method",
                "rife",
                "--target-fps",
                str(fps),
                "--loop-mode",
                "none",
                "--out-dir",
                str(temp_out_dir),
                "--run-name",
                run_name,
                "--filename-prefix",
                default_filename_prefix(run_name),
            ],
            timeout_s=timeout_s,
        )
    )
    shutil.copy2(result_path, target_video)


def system_stats_ready(base_url: str) -> bool:
    try:
        with urlopen(f"{base_url.rstrip('/')}/system_stats", timeout=5) as response:
            return int(getattr(response, "status", 200) or 200) == 200
    except Exception:
        return False


def relaunch_dedicated_comfy(base_url: str) -> dict[str, object]:
    parsed = urlparse(base_url)
    port = parsed.port or 8010
    if port != 8010:
        return {"ok": False, "reason": "relaunch_only_configured_for_8010"}
    launch_script = script_path("launch_comfy_headless.py")
    stdout_log = DEFAULT_COMFY_USER / "comfyui_8010.log"
    stderr_log = DEFAULT_COMFY_USER / "comfyui_8010.err.log"
    try:
        pid = run_checked(
            [
                "python",
                str(launch_script),
                "--python",
                str(DEFAULT_COMFY_PYTHON),
                "--main",
                str(DEFAULT_COMFY_MAIN),
                "--base-dir",
                str(DEFAULT_COMFY_BASE),
                "--user-dir",
                str(DEFAULT_COMFY_USER),
                "--input-dir",
                str(DEFAULT_COMFY_INPUT),
                "--output-dir",
                str(DEFAULT_COMFY_OUTPUT),
                "--front-end-root",
                str(DEFAULT_COMFY_FRONTEND),
                "--extra-models-config",
                str(DEFAULT_COMFY_EXTRA_MODELS),
                "--database-url",
                DEFAULT_COMFY_DB_URL,
                "--host",
                parsed.hostname or "127.0.0.1",
                "--port",
                str(port),
                "--timeout",
                "240",
                "--stdout-log",
                str(stdout_log),
                "--stderr-log",
                str(stderr_log),
                "--enable-manager",
            ]
        )
        time.sleep(2)
        return {
            "ok": system_stats_ready(base_url),
            "pid": pid,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        }
    except subprocess.CalledProcessError as exc:
        return {
            "ok": False,
            "returncode": exc.returncode,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }


def render_attempts(width: int, height: int, length: int, quality_preset: str) -> list[dict[str, object]]:
    candidates = [
        {"width": width, "height": height, "length": length, "quality_preset": quality_preset, "label": "requested"},
        {"width": width, "height": height, "length": min(length, 97), "quality_preset": quality_preset, "label": "requested_shorter"},
        {"width": 704, "height": 1248, "length": min(length, 97), "quality_preset": quality_preset, "label": "portrait_704x1248"},
        {"width": 640, "height": 992, "length": min(length, 97), "quality_preset": quality_preset, "label": "stable_640x992_len97"},
        {"width": 640, "height": 992, "length": 81, "quality_preset": quality_preset, "label": "stable_640x992_len81"},
        {"width": 640, "height": 992, "length": 65, "quality_preset": "fast", "label": "floor_fast65"},
    ]
    unique: list[dict[str, object]] = []
    seen: set[tuple[int, int, int, str]] = set()
    for candidate in candidates:
        key = (
            int(candidate["width"]),
            int(candidate["height"]),
            int(candidate["length"]),
            str(candidate["quality_preset"]),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def run_wan_profile(
    *,
    args: argparse.Namespace,
    render_script: Path,
    profile: dict[str, object],
    staged_path: Path,
    raw_dir: Path,
    job_slug: str,
) -> tuple[Path, list[dict[str, object]]]:
    attempts_log: list[dict[str, object]] = []
    last_error: subprocess.CalledProcessError | None = None
    for attempt_index, attempt in enumerate(
        render_attempts(args.width, args.height, args.length, str(profile["quality_preset"])),
        start=1,
    ):
        attempt_suffix = (
            f"{profile['slug']}_{attempt['label']}_{attempt['width']}x{attempt['height']}_len{attempt['length']}_"
            f"{attempt['quality_preset']}"
        )
        raw_run_name = f"{job_slug}_{attempt_suffix}"
        cmd = [
            "python",
            str(render_script),
            "--base-url",
            args.base_url,
            "--start-image",
            staged_path.name,
            "--end-image",
            staged_path.name,
            "--width",
            str(attempt["width"]),
            "--height",
            str(attempt["height"]),
            "--length",
            str(attempt["length"]),
            "--fps",
            str(args.fps),
            "--positive",
            str(profile["positive"]),
            "--negative",
            str(profile["negative"]),
            "--quality-preset",
            str(attempt["quality_preset"]),
            "--seed",
            str(profile["seed"]),
            "--clip-device",
            "cpu",
            "--vae-device",
            "cuda:0",
            "--high-noise-device",
            "cuda:1",
            "--low-noise-device",
            "cuda:0",
            "--filename-prefix",
            default_filename_prefix(raw_run_name),
            "--out-dir",
            str(raw_dir),
            "--run-name",
            raw_run_name,
        ]
        try:
            raw_video = Path(run_checked(cmd, timeout_s=args.raw_timeout_seconds))
            attempts_log.append(
                {
                    "index": attempt_index,
                    "status": "completed",
                    "run_name": raw_run_name,
                    **attempt,
                    "raw_video": str(raw_video),
                }
            )
            return raw_video, attempts_log
        except subprocess.CalledProcessError as exc:
            last_error = exc
            attempt_record: dict[str, object] = {
                "index": attempt_index,
                "status": "failed",
                "run_name": raw_run_name,
                **attempt,
                "returncode": exc.returncode,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            }
            result_json = raw_dir / f"{raw_run_name}.result.json"
            error_json = raw_dir / f"{raw_run_name}.error.json"
            if result_json.exists():
                attempt_record["result_json"] = str(result_json)
                try:
                    attempt_record["result"] = json.loads(result_json.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if error_json.exists():
                attempt_record["error_json"] = str(error_json)
                try:
                    attempt_record["error"] = json.loads(error_json.read_text(encoding="utf-8"))
                except Exception:
                    pass
            comfy_healthy = system_stats_ready(args.base_url)
            attempt_record["comfy_healthy_after_failure"] = comfy_healthy
            if not comfy_healthy:
                relaunch = relaunch_dedicated_comfy(args.base_url)
                attempt_record["comfy_relaunch"] = relaunch
            attempts_log.append(attempt_record)
            time.sleep(2)
    if last_error is None:
        raise RuntimeError("render_attempts_produced_no_runs")
    raise last_error


def run_profile_followup(
    *,
    args: argparse.Namespace,
    profile: dict[str, object],
    raw_video: Path,
    raw_attempts: list[dict[str, object]],
    raw_review: Path,
    job_dir: Path,
    manifest: dict[str, object],
    audio_16k: Path,
    musetalk_script: Path,
    review_script: Path,
    asr_script: Path,
    multilane_review_script: Path,
) -> dict[str, object]:
    slug = str(profile["slug"])
    lipsync_dir = job_dir / "06_lipsync" / slug
    lipsync_name = f"{manifest['job_slug']}_{slug}_{args.voice}_musetalk"
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
                "--video-prep",
                args.musetalk_video_prep,
            ],
            timeout_s=args.musetalk_timeout_seconds,
        )
    )
    spoken_review = job_dir / "03_review" / f"{spoken_video.stem}_review_sheet.jpg"
    run_checked(["python", str(review_script), str(spoken_video), str(spoken_review), "--count", "8", "--cols", "4"])

    qc_dir = job_dir / "07_asr_qc"
    run_checked(
        [
            "python",
            str(asr_script),
            str(spoken_video),
            "--out-dir",
            str(qc_dir),
            "--run-name",
            spoken_video.stem,
            "--expected-text",
            args.speech_text,
        ]
    )

    exports_dir = job_dir / "09_exports"
    export_base = (
        f"PENNY_{manifest['created_at_local'][:10].replace('-', '')}_"
        f"{manifest['job_slug']}_{slug}_{args.voice}_musetalk"
    )
    export_targets: dict[str, str] = {}
    for fps in (25, 30, 60):
        target = exports_dir / f"{export_base}_{fps}fps.mp4"
        if fps == 25:
            export_interpolated(spoken_video, target, fps)
        else:
            run_vfi_master(
                spoken_video,
                target,
                base_url=args.base_url,
                out_dir=job_dir / "09_exports",
                run_name=f"{spoken_video.stem}_rife_{fps}",
                fps=fps,
                timeout_s=args.vfi_timeout_seconds,
            )
        export_targets[f"{fps}fps"] = str(target)
    subtitle_source = qc_dir / f"{spoken_video.stem}.transcript.srt"
    subtitle_target = None
    if subtitle_source.exists():
        subtitle_target = exports_dir / f"{export_base}.srt"
        shutil.copy2(subtitle_source, subtitle_target)

    review_json = job_dir / "03_review" / f"{slug}_multilane_review_report.json"
    review_md = job_dir / "03_review" / f"{slug}_multilane_review_report.md"
    run_checked(
        [
            "python",
            str(multilane_review_script),
            "--review-image",
            str(spoken_review),
            "--video",
            export_targets["60fps"],
            "--evaluation",
            str(job_dir / "10_sidecars" / "heterogeneous_eval_before.json"),
            "--out-json",
            str(review_json),
            "--out-md",
            str(review_md),
        ]
    )

    return {
        "slug": slug,
        "notes": profile["notes"],
        "raw_video": str(raw_video),
        "raw_review_sheet": str(raw_review),
        "raw_attempts": raw_attempts,
        "spoken_video": str(spoken_video),
        "spoken_review_sheet": str(spoken_review),
        "qc_json": str(qc_dir / f"{spoken_video.stem}.asr_qc.json"),
        "exports": export_targets,
        "subtitle": str(subtitle_target) if subtitle_target else None,
        "multilane_review_json": str(review_json),
        "multilane_review_md": str(review_md),
    }


def build_profiles() -> list[dict[str, object]]:
    negative = (
        "overexposed, static frame, blurry face, deformed face, distorted anatomy, extra fingers, malformed hands, "
        "warped earrings, background crowd, text, subtitle, worst quality, low quality, jpeg artifacts, open mouth, "
        "talking mouth, teeth, speech pose, generic face drift, asymmetrical eyes, plastic skin, mannequin posture, "
        "body distortion, frozen shoulders, rigid torso, drifted eye color"
    )
    return [
        {
            "slug": "torso_sway_quality129",
            "seed": 984937593540091,
            "quality_preset": "quality",
            "positive": (
                "Penny, preserving her canonical bright blue eyes, fair warm complexion, auburn softly wavy hair, "
                "balanced natural proportions, and grounded warm presence. She is wearing the same sparkling red halter "
                "dress and gold earrings as the approved reference image. Living portrait with gentle full upper-body "
                "engagement: natural breathing, subtle collarbone rise, slight shoulder sway, tiny torso weight shift, "
                "soft head tilt, delicate earring movement, faint hair flutter, and steady warm eye contact. Keep the "
                "mouth closed and relaxed because speech is added later. Maintain clean identity, realistic skin, "
                "natural anatomy, stable framing, and settle close to the opening pose by the final frames."
            ),
            "negative": negative,
            "notes": "Soft torso sway baseline for cleaner downstream lip-sync.",
        },
        {
            "slug": "glance_return_quality129",
            "seed": 984937593540092,
            "quality_preset": "quality",
            "positive": (
                "Penny, preserving her canonical bright blue eyes, fair warm complexion, auburn softly wavy hair, "
                "balanced natural proportions, and grounded warm presence. She is wearing the same sparkling red halter "
                "dress and gold earrings as the approved reference image. Elegant speaking-ready portrait with gentle "
                "shoulder shift, a slight turn of the head away from camera, a natural glance back toward the viewer, "
                "soft breathing through the chest and shoulders, subtle earring sway, and controlled poised expression. "
                "Closed mouth only, not speaking yet. Preserve exact face fidelity, realistic skin detail, and clean "
                "continuity while returning near the initial pose by the end."
            ),
            "negative": negative,
            "notes": "Adds more head/eye engagement without forcing heavy motion.",
        },
        {
            "slug": "statement_ready_quality129",
            "seed": 984937593540093,
            "quality_preset": "quality",
            "positive": (
                "Penny, preserving her canonical bright blue eyes, fair warm complexion, auburn softly wavy hair, "
                "balanced natural proportions, and grounded warm presence. She is wearing the same sparkling red halter "
                "dress and gold earrings as the approved reference image. Calm presenter-like upper-body motion: gentle "
                "breathing, subtle posture reset, soft shoulder and upper-torso movement, slight chin lift, natural "
                "micro-smile, delicate earring swing, and composed confident gaze. Mouth closed and neutral because the "
                "spoken pass comes later. Keep the body alive, not rigid, while preserving identity, framing, and ending "
                "close to the starting composition."
            ),
            "negative": negative,
            "notes": "Speaking-ready body motion without pre-baked mouth movement.",
        },
    ]


def main() -> int:
    args = parse_args()
    init_script = script_path("init_media_job.py")
    stage_script = script_path("stage_reference_frame.py")
    render_script = script_path("run_wan_flf2v.py")
    review_script = script_path("review_video_result.py")
    tts_script = script_path("synthesize_kokoro_tts.py")
    musetalk_script = script_path("run_musetalk_pass.py")
    asr_script = script_path("analyze_spoken_clip.py")
    evaluate_script = DEFAULT_WORKBENCH_TOOLS / "evaluate_heterogeneous_media_pipeline.py"
    feeder_script = DEFAULT_WORKBENCH_TOOLS / "set_mx3_media_assist_mode.py"
    multilane_review_script = DEFAULT_WORKBENCH_TOOLS / "build_multilane_review_report.py"

    job_dir = Path(
        run_checked(
            [
                "python",
                str(init_script),
                str(args.source),
                "--job-name",
                args.job_name,
                "--root",
                str(args.root),
                "--subject",
                "Penny",
                "--continuity-profile",
                "penny_canon_v1",
                "--expected-dialogue",
                args.speech_text,
                "--notes",
                "Recursive refinement batch using Jessica voice, longer quality Wan motion, MX3 feeder assist, "
                "and multi-lane review artifacts.",
            ]
        )
    )

    manifest_path = job_dir / "10_sidecars" / "job_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    comfy_input = DEFAULT_COMFY_INPUT
    staged_path = job_dir / "01_staged" / f"{slugify(args.job_name)}_{args.width}x{args.height}.jpg"
    run_checked(
        [
            "python",
            str(stage_script),
            str(args.source),
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

    run_checked(
        [
            "python",
            str(feeder_script),
            "--mode",
            "enable",
            "--out",
            str(job_dir / "10_sidecars" / "mx3_media_assist_mode_enable.json"),
        ]
    )
    run_checked(
        [
            "python",
            str(evaluate_script),
            "--review-image",
            str(staged_path),
            "--out",
            str(job_dir / "10_sidecars" / "heterogeneous_eval_before.json"),
        ]
    )

    audio_dir = job_dir / "05_audio_tts"
    audio_base = f"{manifest['job_slug']}_{args.voice}"
    raw_audio = audio_dir / f"{audio_base}.wav"
    audio_meta = job_dir / "10_sidecars" / f"{audio_base}.tts.json"
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

    profiles = build_profiles()[: max(args.max_profiles, 1)]
    batch_summary: dict[str, object] = {
        "job_dir": str(job_dir),
        "source": str(args.source),
        "staged_input": str(staged_path),
        "speech_text": args.speech_text,
        "voice": args.voice,
        "profiles": [],
        "failures": [],
    }

    first_successful_review: Path | None = None
    futures: dict[concurrent.futures.Future[dict[str, object]], str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(args.parallel_followups, 1)) as executor:
        for profile in profiles:
            slug = str(profile["slug"])
            try:
                raw_dir = job_dir / "02_raw_forward"
                raw_video, raw_attempts = run_wan_profile(
                    args=args,
                    render_script=render_script,
                    profile=profile,
                    staged_path=staged_path,
                    raw_dir=raw_dir,
                    job_slug=manifest["job_slug"],
                )
                raw_review = job_dir / "03_review" / f"{raw_video.stem}_review_sheet.jpg"
                run_checked(["python", str(review_script), str(raw_video), str(raw_review), "--count", "8", "--cols", "4"])
                future = executor.submit(
                    run_profile_followup,
                    args=args,
                    profile=profile,
                    raw_video=raw_video,
                    raw_attempts=raw_attempts,
                    raw_review=raw_review,
                    job_dir=job_dir,
                    manifest=manifest,
                    audio_16k=audio_16k,
                    musetalk_script=musetalk_script,
                    review_script=review_script,
                    asr_script=asr_script,
                    multilane_review_script=multilane_review_script,
                )
                futures[future] = slug
                if first_successful_review is None:
                    first_successful_review = raw_review
            except subprocess.CalledProcessError as exc:
                batch_summary["failures"].append(
                    {
                        "slug": slug,
                        "notes": profile["notes"],
                        "command": exc.cmd,
                        "returncode": exc.returncode,
                        "stdout": exc.stdout,
                        "stderr": exc.stderr,
                    }
                )
            except subprocess.TimeoutExpired as exc:
                batch_summary["failures"].append(
                    {
                        "slug": slug,
                        "notes": profile["notes"],
                        "command": exc.cmd,
                        "timeout_seconds": exc.timeout,
                        "stdout": exc.stdout,
                        "stderr": exc.stderr,
                    }
                )
        for future in concurrent.futures.as_completed(futures):
            slug = futures[future]
            try:
                profile_result = future.result()
                batch_summary["profiles"].append(profile_result)
            except subprocess.CalledProcessError as exc:
                batch_summary["failures"].append(
                    {
                        "slug": slug,
                        "command": exc.cmd,
                        "returncode": exc.returncode,
                        "stdout": exc.stdout,
                        "stderr": exc.stderr,
                    }
                )
            except subprocess.TimeoutExpired as exc:
                batch_summary["failures"].append(
                    {
                        "slug": slug,
                        "command": exc.cmd,
                        "timeout_seconds": exc.timeout,
                        "stdout": exc.stdout,
                        "stderr": exc.stderr,
                    }
                )

    run_checked(
        [
            "python",
            str(evaluate_script),
            "--review-image",
            str(first_successful_review or staged_path),
            "--out",
            str(job_dir / "10_sidecars" / "heterogeneous_eval_after.json"),
        ]
    )

    manifest["status"]["raw_forward_complete"] = True
    manifest["status"]["review_complete"] = True
    manifest["status"]["tts_complete"] = True
    manifest["status"]["lipsync_complete"] = bool(batch_summary["profiles"])
    manifest["status"]["asr_qc_complete"] = bool(batch_summary["profiles"])
    manifest["status"]["final_export_complete"] = bool(batch_summary["profiles"])
    manifest["status"]["baseline_locked"] = False
    manifest["notes"] = (
        manifest.get("notes", "")
        + " Recursive batch completed with three quality variants and structured multi-lane review artifacts."
    ).strip()
    save_json(manifest_path, manifest)
    save_json(job_dir / "10_sidecars" / "recursive_batch_manifest.json", batch_summary)

    if args.open_explorer:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Start-Process explorer.exe '{job_dir / '09_exports'}'"],
            check=False,
        )

    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
