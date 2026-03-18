#!/usr/bin/env python3
"""Run a segmented Penny spoken batch and stitch the finished masters."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
from pathlib import Path

from local_defaults import DEFAULT_COMFY_INPUT, DEFAULT_LANE_BENCHMARKS
from media_pipeline_runtime import (
    append_retry_lineage,
    emit_manifest_event,
    register_segment_plan,
    set_final_export_selection,
    update_manifest,
    update_segment_state,
)
from run_recursive_refinement_batch import (
    DEFAULT_KOKORO_MODEL,
    DEFAULT_KOKORO_VOICES,
    DEFAULT_MUSETALK_REPO,
    DEFAULT_WORKBENCH_TOOLS,
    DEFAULT_WORK_ITEMS,
    build_profiles,
    export_interpolated,
    run_checked,
    run_vfi_master,
    save_json,
    slugify,
    default_filename_prefix,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a segmented Penny spoken batch")
    parser.add_argument("source", type=Path, help="Approved source still")
    parser.add_argument("--job-name", required=True, help="Batch job name")
    parser.add_argument("--speech-text", required=True, help="Dialogue line for the spoken batch")
    parser.add_argument("--root", type=Path, default=DEFAULT_WORK_ITEMS, help="Workbench work-items root")
    parser.add_argument(
        "--base-urls",
        nargs="+",
        default=["http://127.0.0.1:8010", "http://127.0.0.1:8011"],
        help="One or more dedicated Comfy lanes for raw segment rendering",
    )
    parser.add_argument("--width", type=int, default=704, help="Target staged/render width")
    parser.add_argument("--height", type=int, default=1248, help="Target staged/render height")
    parser.add_argument("--stage-mode", choices=("pad", "fit", "crop"), default="pad", help="Stage mode")
    parser.add_argument("--fps", type=float, default=16.0, help="Native Wan fps")
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
    parser.add_argument("--segment-min-frames", type=int, default=16, help="Minimum Wan frames per raw segment")
    parser.add_argument("--segment-max-frames", type=int, default=49, help="Maximum Wan frames per raw segment")
    parser.add_argument("--segment-padding-frames", type=int, default=8, help="Extra Wan frames beyond audio duration")
    parser.add_argument(
        "--segment-mode",
        choices=("sentence", "clause"),
        default="clause",
        help="How aggressively to split dialogue before rendering micro-clips",
    )
    parser.add_argument(
        "--lane-benchmarks",
        type=Path,
        default=DEFAULT_LANE_BENCHMARKS,
        help="JSON file describing measured raw-render lane throughput",
    )
    parser.add_argument(
        "--target-raw-minutes-max",
        type=float,
        default=30.0,
        help="Target maximum wall time for each raw render slice",
    )
    parser.add_argument(
        "--slice-safety-factor",
        type=float,
        default=0.8,
        help="Conservative multiplier applied to measured max-frames budgets so slices stay comfortably under target time",
    )
    parser.add_argument("--parallel-raw-workers", type=int, default=2, help="How many raw segment lanes may run at once")
    parser.add_argument("--raw-timeout-seconds", type=int, default=2400, help="Hard timeout for each raw Wan render")
    parser.add_argument("--musetalk-timeout-seconds", type=int, default=2400, help="Hard timeout for each MuseTalk pass")
    parser.add_argument("--vfi-timeout-seconds", type=int, default=2400, help="Hard timeout for each VFI master pass")
    parser.add_argument("--open-explorer", action="store_true", help="Open the final export folder")
    return parser.parse_args()


def split_sentences(text: str) -> list[str]:
    pieces = [piece.strip() for piece in re.split(r"(?<=[.!?])\s+", text.strip()) if piece.strip()]
    if pieces:
        return pieces
    fallback = [piece.strip() for piece in re.split(r"\s*,\s*", text.strip()) if piece.strip()]
    return fallback or [text.strip()]


def split_dialogue(text: str, mode: str) -> list[str]:
    sentences = split_sentences(text)
    if mode == "sentence":
        return sentences
    segments: list[str] = []
    for sentence in sentences:
        if len(sentence.split()) <= 4:
            segments.append(sentence)
            continue
        clauses = [piece.strip(" ,") for piece in re.split(r",\s*", sentence) if piece.strip(" ,")]
        merged: list[str] = []
        for clause in clauses:
            if merged and len(clause.split()) <= 2:
                merged[-1] = f"{merged[-1]} {clause}".strip()
            else:
                merged.append(clause)
        if merged:
            segments.extend(merged)
        else:
            segments.append(sentence)
    return segments or sentences


def split_text_midpoint(text: str) -> list[str]:
    words = text.strip().split()
    if len(words) <= 3:
        return [text.strip()]
    midpoint = len(words) // 2
    split_index = midpoint
    for idx in range(midpoint, len(words) - 1):
        token = words[idx].strip(",;:.!?").lower()
        if token in {"and", "but", "then", "while", "because", "with"}:
            split_index = idx
            break
    left = " ".join(words[:split_index]).strip(" ,")
    right = " ".join(words[split_index:]).strip(" ,")
    if not left or not right:
        left = " ".join(words[:midpoint]).strip(" ,")
        right = " ".join(words[midpoint:]).strip(" ,")
    if not left or not right:
        return [text.strip()]
    return [left, right]


def ffprobe_duration_seconds(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return float((completed.stdout or "0").strip() or 0.0)


def frames_for_audio(duration_seconds: float, fps: float, min_frames: int, max_frames: int, padding_frames: int) -> int:
    requested = int(round(duration_seconds * fps)) + max(padding_frames, 0)
    return max(min_frames, min(max_frames, requested))


def load_lane_benchmarks(
    path: Path,
    base_urls: list[str],
    target_minutes_max: float,
    safety_factor: float,
) -> dict[str, dict[str, object]]:
    defaults = {
        "http://127.0.0.1:8011": {
            "label": "nvidia_5060ti",
            "seconds_per_step": 116.68,
            "steps_per_quality_render": 20,
        },
        "http://127.0.0.1:8010": {
            "label": "nvidia_4060ti",
            "seconds_per_step": 325.73,
            "steps_per_quality_render": 20,
        },
    }
    loaded = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for lane in payload.get("lanes", []):
                if not isinstance(lane, dict):
                    continue
                base_url = str(lane.get("base_url") or "").strip()
                if base_url:
                    loaded[base_url] = lane
        except Exception:
            loaded = {}
    result: dict[str, dict[str, object]] = {}
    for base_url in base_urls:
        lane = dict(defaults.get(base_url, {}))
        lane.update(loaded.get(base_url, {}))
        seconds_per_step = float(lane.get("seconds_per_step") or 180.0)
        steps_per_quality_render = int(lane.get("steps_per_quality_render") or 20)
        observed_frames = max(1, int(lane.get("observed_frames") or 49))
        raw_max_frames = (target_minutes_max * 60.0) / ((seconds_per_step * steps_per_quality_render) / observed_frames)
        max_frames = int(round(raw_max_frames * max(0.4, min(1.0, safety_factor))))
        lane["seconds_per_step"] = seconds_per_step
        lane["steps_per_quality_render"] = steps_per_quality_render
        lane["observed_frames"] = observed_frames
        lane["target_minutes_max"] = target_minutes_max
        lane["slice_safety_factor"] = safety_factor
        lane["max_frames_at_target_minutes"] = max(16, max_frames)
        result[base_url] = lane
    return result


def estimate_lane_minutes(frames: int, lane: dict[str, object]) -> float:
    observed_frames = max(1, int(lane.get("observed_frames") or lane.get("max_frames_at_target_minutes") or frames))
    seconds_per_step = float(lane.get("seconds_per_step") or 180.0)
    steps_per_quality_render = int(lane.get("steps_per_quality_render") or 20)
    seconds = (frames / observed_frames) * (seconds_per_step * steps_per_quality_render)
    return seconds / 60.0


def assign_segments_to_lanes(
    segments: list[dict[str, object]],
    lane_benchmarks: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    lane_loads = {base_url: 0.0 for base_url in lane_benchmarks}
    planned: list[dict[str, object]] = []
    for segment in sorted(segments, key=lambda item: float(item["duration_seconds"]), reverse=True):
        requested_frames = int(segment["requested_frames"])
        eligible_lanes = [
            base_url
            for base_url, lane in lane_benchmarks.items()
            if requested_frames <= int(lane.get("max_frames_at_target_minutes") or requested_frames)
        ]
        if not eligible_lanes:
            eligible_lanes = sorted(
                lane_benchmarks.keys(),
                key=lambda base_url: int(lane_benchmarks[base_url].get("max_frames_at_target_minutes") or 0),
                reverse=True,
            )
        best_lane = min(
            eligible_lanes,
            key=lambda base_url: (
                lane_loads[base_url],
                -int(lane_benchmarks[base_url].get("max_frames_at_target_minutes") or 0),
            ),
        )
        lane = lane_benchmarks[best_lane]
        capped_frames = min(requested_frames, int(lane.get("max_frames_at_target_minutes") or requested_frames))
        record = dict(segment)
        record["lane_base_url"] = best_lane
        record["lane_label"] = lane.get("label")
        record["frames"] = capped_frames
        record["frames_capped"] = capped_frames != int(segment["requested_frames"])
        record["estimated_lane_minutes"] = round(estimate_lane_minutes(capped_frames, lane), 2)
        lane_loads[best_lane] += float(record["estimated_lane_minutes"])
        planned.append(record)
    planned.sort(key=lambda item: int(item["index"]))
    return planned


def summarize_lane_plan(
    segment_plan: list[dict[str, object]], lane_benchmarks: dict[str, dict[str, object]]
) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for base_url, lane in lane_benchmarks.items():
        assigned = [segment for segment in segment_plan if str(segment.get("lane_base_url")) == base_url]
        summary[base_url] = {
            "label": lane.get("label"),
            "gpu_name": lane.get("gpu_name"),
            "segment_count": len(assigned),
            "frames_total": sum(int(segment.get("frames") or 0) for segment in assigned),
            "estimated_minutes_total": round(
                sum(float(segment.get("estimated_lane_minutes") or 0.0) for segment in assigned), 2
            ),
            "segment_indices": [int(segment.get("index") or 0) for segment in assigned],
        }
    return summary


def manifest_segment_record(segment: dict[str, object]) -> dict[str, object]:
    profile = segment.get("profile", {})
    return {
        "index": int(segment["index"]),
        "text": str(segment["text"]),
        "duration_seconds": float(segment["duration_seconds"]),
        "requested_frames": int(segment["requested_frames"]),
        "frames": int(segment["frames"]),
        "frames_capped": bool(segment.get("frames_capped", False)),
        "estimated_lane_minutes": float(segment.get("estimated_lane_minutes") or 0.0),
        "lane_base_url": str(segment.get("lane_base_url") or ""),
        "lane_label": str(segment.get("lane_label") or ""),
        "audio": str(segment.get("audio") or ""),
        "audio_16k": str(segment.get("audio_16k") or ""),
        "profile_slug": str(profile.get("slug") or ""),
    }


def review_decision_from_payload(payload: dict[str, object]) -> str:
    structured = payload.get("structured_review")
    text = json.dumps(structured or payload, ensure_ascii=True).lower()
    problem_tokens = (
        "flash",
        "flashing",
        "blur",
        "blurry",
        "rigid",
        "drift",
        "artifact",
        "asymmetrical",
    )
    return "retry_recommended" if any(token in text for token in problem_tokens) else "candidate_ok"


def dispatch_slice_review(
    *,
    review_script: Path,
    multilane_review_script: Path,
    review_dir: Path,
    sidecar_dir: Path,
    evaluation_path: Path,
    raw_video: Path,
    segment_index: int,
) -> dict[str, object]:
    raw_review = review_dir / f"{raw_video.stem}_review_sheet.jpg"
    run_checked(["python", str(review_script), str(raw_video), str(raw_review), "--count", "8", "--cols", "4"])
    review_json = sidecar_dir / f"segment_{segment_index:02d}_multilane_review.json"
    review_md = review_dir / f"segment_{segment_index:02d}_multilane_review.md"
    run_checked(
        [
            "python",
            str(multilane_review_script),
            "--review-image",
            str(raw_review),
            "--video",
            str(raw_video),
            "--evaluation",
            str(evaluation_path),
            "--out-json",
            str(review_json),
            "--out-md",
            str(review_md),
        ]
    )
    payload = json.loads(review_json.read_text(encoding="utf-8"))
    review_decision = review_decision_from_payload(payload)
    return {
        "raw_review": str(raw_review),
        "multilane_review_json": str(review_json),
        "multilane_review_md": str(review_md),
        "structured_review": payload.get("structured_review"),
        "shockwave_review": payload.get("shockwave_review"),
        "mx3_review": payload.get("mx3_review"),
        "review_decision": review_decision,
        "retry_suggestion": "re-render_smaller_slice" if review_decision != "candidate_ok" else None,
    }


def render_segment_with_events(
    *,
    manifest_path: Path,
    args: argparse.Namespace,
    render_script: Path,
    profile: dict[str, object],
    staged_path: Path,
    raw_dir: Path,
    job_slug: str,
    segment_index: int,
    segment_frames: int,
    base_url: str,
) -> dict[str, object]:
    emit_manifest_event(
        manifest_path,
        "slice.started",
        {"segment_index": segment_index, "frames": segment_frames, "lane_base_url": base_url},
        phase="raw_render",
        status="running",
    )
    update_segment_state(
        manifest_path,
        segment_index,
        {
            "status": "raw_render_running",
            "frames": segment_frames,
            "lane_base_url": base_url,
        },
    )
    try:
        result = render_segment(
            args=args,
            render_script=render_script,
            profile=profile,
            staged_path=staged_path,
            raw_dir=raw_dir,
            job_slug=job_slug,
            segment_index=segment_index,
            segment_frames=segment_frames,
            base_url=base_url,
        )
    except Exception as exc:  # noqa: BLE001
        append_retry_lineage(
            manifest_path,
            segment_index=segment_index,
            reason="raw_render_failed",
            context={"lane_base_url": base_url, "error": str(exc)},
        )
        emit_manifest_event(
            manifest_path,
            "retry.queued",
            {"segment_index": segment_index, "lane_base_url": base_url, "error": str(exc)},
            phase="raw_render",
            status="failed",
        )
        update_segment_state(
            manifest_path,
            segment_index,
            {
                "status": "raw_render_failed",
                "lane_base_url": base_url,
                "error": str(exc),
                "retry_suggestion": "re-render_smaller_slice",
            },
        )
        raise
    emit_manifest_event(
        manifest_path,
        "slice.completed",
        {
            "segment_index": segment_index,
            "lane_base_url": base_url,
            "raw_video": str(result["raw_video"]),
            "frames": segment_frames,
        },
        phase="raw_render",
        status="completed",
    )
    update_segment_state(
        manifest_path,
        segment_index,
        {
            "status": "raw_render_complete",
            "lane_base_url": base_url,
            "raw_video": str(result["raw_video"]),
            "frames": segment_frames,
        },
    )
    return result


def build_tts_segment_records(
    *,
    args: argparse.Namespace,
    tts_script: Path,
    audio_dir: Path,
    sidecar_dir: Path,
    job_slug: str,
    profiles: list[dict[str, object]],
    sentences: list[str],
    split_frame_budget: int,
) -> list[dict[str, object]]:
    pending = [{"text": sentence, "profile_index": idx} for idx, sentence in enumerate(sentences, start=1)]
    accepted: list[dict[str, object]] = []
    sequence = 1
    while pending:
        current = pending.pop(0)
        sentence_slug = f"segment_{sequence:02d}"
        raw_audio = audio_dir / f"{job_slug}_{sentence_slug}_{args.voice}.wav"
        audio_meta = sidecar_dir / f"{job_slug}_{sentence_slug}_{args.voice}.tts.json"
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
                str(current["text"]),
                "--meta-out",
                str(audio_meta),
            ]
        )
        audio_16k = audio_dir / f"{raw_audio.stem}_16k.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_audio), "-ac", "1", "-ar", "16000", str(audio_16k)],
            check=True,
            capture_output=True,
            text=True,
        )
        duration_seconds = ffprobe_duration_seconds(raw_audio)
        requested_frames = frames_for_audio(
            duration_seconds,
            args.fps,
            args.segment_min_frames,
            args.segment_max_frames,
            args.segment_padding_frames,
        )
        if requested_frames > split_frame_budget:
            split_parts = split_text_midpoint(str(current["text"]))
            if len(split_parts) > 1:
                for stale in (raw_audio, audio_16k, audio_meta):
                    if stale.exists():
                        stale.unlink()
                pending = (
                    [{"text": split_parts[0], "profile_index": current["profile_index"]}]
                    + [{"text": split_parts[1], "profile_index": current["profile_index"]}]
                    + pending
                )
                continue
        accepted.append(
            {
                "index": sequence,
                "text": str(current["text"]),
                "profile": profiles[(int(current["profile_index"]) - 1) % len(profiles)],
                "audio": str(raw_audio),
                "audio_16k": str(audio_16k),
                "duration_seconds": duration_seconds,
                "requested_frames": requested_frames,
            }
        )
        sequence += 1
    return accepted


def stitch_videos(video_paths: list[Path], out_path: Path) -> None:
    if not video_paths:
        raise ValueError("video_paths_required")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if len(video_paths) == 1:
        shutil.copy2(video_paths[0], out_path)
        return
    manifest_path = out_path.with_suffix(".concat.txt")
    manifest_path.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in video_paths),
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
            str(manifest_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def render_segment(
    *,
    args: argparse.Namespace,
    render_script: Path,
    profile: dict[str, object],
    staged_path: Path,
    raw_dir: Path,
    job_slug: str,
    segment_index: int,
    segment_frames: int,
    base_url: str,
) -> dict[str, object]:
    raw_run_name = f"{job_slug}_{profile['slug']}_segment_{segment_index:02d}_len{segment_frames}"
    cmd = [
        "python",
        str(render_script),
        "--base-url",
        base_url,
        "--start-image",
        staged_path.name,
        "--end-image",
        staged_path.name,
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--length",
        str(segment_frames),
        "--fps",
        str(args.fps),
        "--positive",
        str(profile["positive"]),
        "--negative",
        str(profile["negative"]),
        "--quality-preset",
        str(profile["quality_preset"]),
        "--seed",
        str(int(profile["seed"]) + segment_index - 1),
        "--clip-device",
        "cpu",
        "--vae-device",
        "cuda:0",
        "--high-noise-device",
        "cuda:0",
        "--low-noise-device",
        "cuda:0",
        "--filename-prefix",
        default_filename_prefix(raw_run_name),
        "--out-dir",
        str(raw_dir),
        "--run-name",
        raw_run_name,
        "--disable-multigpu-loaders",
    ]
    raw_video = Path(run_checked(cmd, timeout_s=args.raw_timeout_seconds))
    return {
        "segment_index": segment_index,
        "profile_slug": str(profile["slug"]),
        "frames": segment_frames,
        "base_url": base_url,
        "raw_video": str(raw_video),
    }


def main() -> int:
    args = parse_args()
    init_script = Path(__file__).with_name("init_media_job.py")
    stage_script = Path(__file__).with_name("stage_reference_frame.py")
    render_script = Path(__file__).with_name("run_wan_flf2v.py")
    review_script = Path(__file__).with_name("review_video_result.py")
    tts_script = Path(__file__).with_name("synthesize_kokoro_tts.py")
    musetalk_script = Path(__file__).with_name("run_musetalk_pass.py")
    asr_script = Path(__file__).with_name("analyze_spoken_clip.py")
    evaluate_script = DEFAULT_WORKBENCH_TOOLS / "evaluate_heterogeneous_media_pipeline.py"
    feeder_script = DEFAULT_WORKBENCH_TOOLS / "set_mx3_media_assist_mode.py"
    multilane_review_script = DEFAULT_WORKBENCH_TOOLS / "build_multilane_review_report.py"

    sentences = split_dialogue(args.speech_text, args.segment_mode)
    profiles = build_profiles()
    lane_benchmarks = load_lane_benchmarks(
        args.lane_benchmarks,
        args.base_urls,
        args.target_raw_minutes_max,
        args.slice_safety_factor,
    )

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
                "--job-type",
                "full_text_to_mp4",
                "--continuity-profile",
                "penny_canon_v1",
                "--expected-dialogue",
                args.speech_text,
                "--notes",
                "Segmented recursive refinement batch using Jessica voice, sentence-sized Wan motion slices, "
                "stitched spoken masters, MX3 feeder assist, and multi-lane review artifacts.",
                "--voice-id",
                args.voice,
                "--voice-language",
                args.tts_lang,
                "--voice-speed",
                str(args.tts_speed),
                "--voice-pitch-shift",
                str(args.tts_pitch_shift),
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
    raw_dir = job_dir / "02_raw_forward"
    review_dir = job_dir / "03_review"
    lipsync_dir = job_dir / "06_lipsync"
    qc_dir = job_dir / "07_asr_qc"
    exports_dir = job_dir / "09_exports"
    sidecar_dir = job_dir / "10_sidecars"
    review_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    lipsync_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    lane_frame_caps = [
        int(lane.get("max_frames_at_target_minutes") or args.segment_max_frames)
        for lane in lane_benchmarks.values()
    ]
    split_frame_budget = int(round(sum(lane_frame_caps) / max(1, len(lane_frame_caps))))
    provisional_segments = build_tts_segment_records(
        args=args,
        tts_script=tts_script,
        audio_dir=audio_dir,
        sidecar_dir=sidecar_dir,
        job_slug=manifest["job_slug"],
        profiles=profiles,
        sentences=sentences,
        split_frame_budget=split_frame_budget,
    )
    segment_plan = assign_segments_to_lanes(provisional_segments, lane_benchmarks)
    lane_plan_summary = summarize_lane_plan(segment_plan, lane_benchmarks)

    raw_results_by_index: dict[int, dict[str, object]] = {}
    review_results_by_index: dict[int, dict[str, object]] = {}
    failed_segments: dict[int, str] = {}
    futures: dict[concurrent.futures.Future[dict[str, object]], dict[str, object]] = {}

    save_json(
        sidecar_dir / "segmented_spoken_batch_plan.json",
        {
            "job_dir": str(job_dir),
            "source": str(args.source),
            "job_slug": manifest["job_slug"],
            "speech_text": args.speech_text,
            "voice": args.voice,
            "base_urls": args.base_urls,
            "lane_benchmarks": lane_benchmarks,
            "lane_plan_summary": lane_plan_summary,
            "split_frame_budget": split_frame_budget,
            "segments": segment_plan,
        },
    )
    register_segment_plan(manifest_path, [manifest_segment_record(segment) for segment in segment_plan])

    def manifest_mutator(current: dict[str, object]) -> dict[str, object]:
        current.setdefault("lane_assignments", {})
        current["lane_assignments"]["raw_render"] = lane_plan_summary
        current["lane_assignments"]["review"] = {
            "radeon_qwen_vl": "http://127.0.0.1:2234",
            "radeon_qwen_text": "http://127.0.0.1:2235",
            "shockwave_vision": "http://127.0.0.1:7088/api/vision/analyze-frame",
        }
        current["lane_assignments"]["qc"] = {
            "mx3": "http://127.0.0.1:9000/api/perception/detect",
            "mx3_pose": "http://127.0.0.1:8787/pose/status",
        }
        current["lane_assignments"]["speech"] = {
            "tts_voice": args.voice,
            "tts_language": args.tts_lang,
            "tts_speed": args.tts_speed,
            "tts_pitch_shift": args.tts_pitch_shift,
            "lip_sync_baseline": "musetalk",
            "lip_sync_upgrade_target": "latentsync",
        }
        current["slice_timing_budget"] = {
            "target_max_minutes": args.target_raw_minutes_max,
            "slice_safety_factor": args.slice_safety_factor,
            "lanes": lane_benchmarks,
        }
        return current

    update_manifest(manifest_path, manifest_mutator)
    for segment in segment_plan:
        emit_manifest_event(
            manifest_path,
            "slice.queued",
            {
                "segment_index": int(segment["index"]),
                "lane_base_url": str(segment["lane_base_url"]),
                "frames": int(segment["frames"]),
                "estimated_lane_minutes": float(segment["estimated_lane_minutes"]),
            },
            phase="raw_render",
            status="queued",
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.parallel_raw_workers, len(args.base_urls)))) as executor:
        for segment in segment_plan:
            future = executor.submit(
                render_segment_with_events,
                manifest_path=manifest_path,
                args=args,
                render_script=render_script,
                profile=dict(segment["profile"]),
                staged_path=staged_path,
                raw_dir=raw_dir,
                job_slug=manifest["job_slug"],
                segment_index=int(segment["index"]),
                segment_frames=int(segment["frames"]),
                base_url=str(segment["lane_base_url"]),
            )
            futures[future] = segment
        for future in concurrent.futures.as_completed(futures):
            segment = futures[future]
            segment_index = int(segment["index"])
            try:
                raw_result = future.result()
                raw_results_by_index[segment_index] = raw_result
            except Exception as exc:  # noqa: BLE001
                failed_segments[segment_index] = str(exc)
                continue

            raw_video = Path(str(raw_result["raw_video"]))
            emit_manifest_event(
                manifest_path,
                "review.queued",
                {"segment_index": segment_index, "raw_video": str(raw_video)},
                phase="review",
                status="queued",
            )
            try:
                review_result = dispatch_slice_review(
                    review_script=review_script,
                    multilane_review_script=multilane_review_script,
                    review_dir=review_dir,
                    sidecar_dir=sidecar_dir,
                    evaluation_path=sidecar_dir / "heterogeneous_eval_before.json",
                    raw_video=raw_video,
                    segment_index=segment_index,
                )
            except Exception as exc:  # noqa: BLE001
                failed_segments[segment_index] = str(exc)
                append_retry_lineage(
                    manifest_path,
                    segment_index=segment_index,
                    reason="slice_review_failed",
                    context={"raw_video": str(raw_video), "error": str(exc)},
                )
                emit_manifest_event(
                    manifest_path,
                    "retry.queued",
                    {"segment_index": segment_index, "raw_video": str(raw_video), "error": str(exc)},
                    phase="review",
                    status="failed",
                )
                update_segment_state(
                    manifest_path,
                    segment_index,
                    {
                        "status": "review_failed",
                        "raw_video": str(raw_video),
                        "retry_suggestion": "inspect_review_pipeline",
                        "error": str(exc),
                    },
                )
                continue

            review_results_by_index[segment_index] = review_result
            update_segment_state(
                manifest_path,
                segment_index,
                {
                    "status": "review_complete",
                    "raw_video": str(raw_video),
                    **review_result,
                },
            )
            emit_manifest_event(
                manifest_path,
                "review.completed",
                {
                    "segment_index": segment_index,
                    "review_decision": review_result["review_decision"],
                    "multilane_review_json": review_result["multilane_review_json"],
                },
                phase="review",
                status="completed",
            )
            emit_manifest_event(
                manifest_path,
                "mx3.qc.completed",
                {
                    "segment_index": segment_index,
                    "mx3_review": review_result.get("mx3_review"),
                    "shockwave_review": review_result.get("shockwave_review"),
                },
                phase="qc",
                status="completed",
            )

    completed_segment_plan = [segment for segment in segment_plan if int(segment["index"]) in raw_results_by_index]
    completed_segment_plan.sort(key=lambda item: int(item["index"]))
    raw_videos_16fps: list[Path] = []
    spoken_videos_25fps: list[Path] = []
    spoken_videos_30fps: list[Path] = []
    spoken_videos_60fps: list[Path] = []

    for segment in completed_segment_plan:
        segment_index = int(segment["index"])
        raw_result = raw_results_by_index[segment_index]
        review_result = review_results_by_index.get(segment_index, {})
        raw_video = Path(str(raw_result["raw_video"]))
        raw_videos_16fps.append(raw_video)
        if review_result:
            segment["review"] = review_result

        spoken_name = f"{manifest['job_slug']}_segment_{segment_index:02d}_{args.voice}_musetalk"
        segment_lipsync_dir = lipsync_dir / f"segment_{segment_index:02d}"
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
                    str(segment["audio_16k"]),
                    "--out-dir",
                    str(segment_lipsync_dir),
                    "--run-name",
                    spoken_name,
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
        spoken_review = review_dir / f"{spoken_video.stem}_review_sheet.jpg"
        run_checked(["python", str(review_script), str(spoken_video), str(spoken_review), "--count", "8", "--cols", "4"])
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
                str(segment["text"]),
            ]
        )

        out25 = exports_dir / f"{spoken_name}_25fps.mp4"
        out30 = exports_dir / f"{spoken_name}_30fps.mp4"
        out60 = exports_dir / f"{spoken_name}_60fps.mp4"
        export_interpolated(spoken_video, out25, 25)
        run_vfi_master(
            spoken_video,
            out30,
            base_url=args.base_urls[0],
            out_dir=exports_dir,
            run_name=f"{spoken_name}_rife_30",
            fps=30,
            timeout_s=args.vfi_timeout_seconds,
        )
        run_vfi_master(
            spoken_video,
            out60,
            base_url=args.base_urls[0],
            out_dir=exports_dir,
            run_name=f"{spoken_name}_rife_60",
            fps=60,
            timeout_s=args.vfi_timeout_seconds,
        )
        spoken_videos_25fps.append(out25)
        spoken_videos_30fps.append(out30)
        spoken_videos_60fps.append(out60)
        segment["raw_video"] = str(raw_video)
        segment["spoken_video"] = str(spoken_video)
        segment["exports"] = {"25fps": str(out25), "30fps": str(out30), "60fps": str(out60)}

    if not completed_segment_plan:
        raise SystemExit("No raw segments completed successfully.")

    stitched_base = f"PENNY_{manifest['created_at_local'][:10].replace('-', '')}_{manifest['job_slug']}_{args.voice}_stitched"
    raw_master = exports_dir / f"{stitched_base}_raw16fps.mp4"
    master_25 = exports_dir / f"{stitched_base}_25fps.mp4"
    master_30 = exports_dir / f"{stitched_base}_30fps.mp4"
    master_60 = exports_dir / f"{stitched_base}_60fps.mp4"
    stitch_videos(raw_videos_16fps, raw_master)
    stitch_videos(spoken_videos_25fps, master_25)
    stitch_videos(spoken_videos_30fps, master_30)
    stitch_videos(spoken_videos_60fps, master_60)

    final_review = review_dir / f"{master_60.stem}_review_sheet.jpg"
    run_checked(["python", str(review_script), str(master_60), str(final_review), "--count", "8", "--cols", "4"])
    final_asr = run_checked(
        [
            "python",
            str(asr_script),
            str(master_60),
            "--out-dir",
            str(qc_dir),
            "--run-name",
            master_60.stem,
            "--expected-text",
            args.speech_text,
        ]
    )
    review_json = review_dir / f"{master_60.stem}_multilane_review_report.json"
    review_md = review_dir / f"{master_60.stem}_multilane_review_report.md"
    run_checked(
        [
            "python",
            str(multilane_review_script),
            "--review-image",
            str(final_review),
            "--video",
            str(master_60),
            "--evaluation",
            str(sidecar_dir / "heterogeneous_eval_before.json"),
            "--out-json",
            str(review_json),
            "--out-md",
            str(review_md),
        ]
    )

    update_manifest(
        manifest_path,
        lambda current: {
            **current,
            "status": {
                **current.get("status", {}),
                "raw_forward_complete": True,
                "review_complete": True,
                "tts_complete": True,
                "lipsync_complete": True,
                "asr_qc_complete": True,
                "final_export_complete": True,
                "baseline_locked": False,
            },
        },
    )
    set_final_export_selection(
        manifest_path,
        export_path=master_60,
        export_kind="stitched_master_60fps",
        review_decision="candidate_selected",
        notes="Current best stitched Jessica baseline pending further LatentSync refinement.",
    )
    emit_manifest_event(
        manifest_path,
        "candidate.selected",
        {"export_path": str(master_60), "export_kind": "stitched_master_60fps"},
        phase="final_export",
        status="selected",
    )
    save_json(
        sidecar_dir / "segmented_spoken_batch_manifest.json",
        {
            "job_dir": str(job_dir),
            "source": str(args.source),
            "speech_text": args.speech_text,
            "voice": args.voice,
            "base_urls": args.base_urls,
            "lane_benchmarks": lane_benchmarks,
            "lane_plan_summary": lane_plan_summary,
            "split_frame_budget": split_frame_budget,
            "segments": segment_plan,
            "completed_segments": [int(segment["index"]) for segment in completed_segment_plan],
            "failed_segments": failed_segments,
            "final_exports": {
                "raw16fps": str(raw_master),
                "25fps": str(master_25),
                "30fps": str(master_30),
                "60fps": str(master_60),
            },
            "final_review_sheet": str(final_review),
            "final_asr_qc": final_asr,
            "multilane_review_json": str(review_json),
            "multilane_review_md": str(review_md),
        },
    )

    if args.open_explorer:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Start-Process explorer.exe '{exports_dir}'"],
            check=False,
        )

    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
