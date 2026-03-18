#!/usr/bin/env python3
"""Run local Whisper ASR QC on a spoken clip and compare it to the expected line."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import whisper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a spoken clip with local Whisper")
    parser.add_argument("input", type=Path, help="Input video or audio file")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory to write QC artifacts")
    parser.add_argument("--run-name", default="", help="Base output name; defaults to input stem")
    parser.add_argument("--model", default="base.en", help="Whisper model name")
    parser.add_argument("--language", default="en", help="Language hint")
    parser.add_argument("--expected-text", default="", help="Expected spoken line")
    parser.add_argument("--expected-text-file", type=Path, help="Path to expected spoken line text file")
    parser.add_argument("--pass-threshold", type=float, default=0.88, help="Similarity threshold for pass")
    parser.add_argument("--warn-threshold", type=float, default=0.75, help="Similarity threshold for warn")
    parser.add_argument("--word-timestamps", action="store_true", help="Request word-level timestamps when supported")
    return parser.parse_args()


def run_ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
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
        check=True,
        capture_output=True,
        text=True,
    )
    return float((result.stdout or "0").strip() or 0.0)


def extract_audio(input_path: Path, output_wav: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output_wav),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def normalize_text(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return " ".join(cleaned.split())


def compare_text(expected: str, actual: str) -> dict[str, Any]:
    expected_norm = normalize_text(expected)
    actual_norm = normalize_text(actual)
    matcher = SequenceMatcher(None, expected_norm, actual_norm)
    expected_words = expected_norm.split()
    actual_words = actual_norm.split()
    expected_counts = Counter(expected_words)
    actual_counts = Counter(actual_words)

    shared = []
    for token in sorted(set(expected_counts) | set(actual_counts)):
        count = min(expected_counts[token], actual_counts[token])
        if count:
            shared.extend([token] * count)

    missing = []
    for token, count in expected_counts.items():
        delta = count - actual_counts[token]
        if delta > 0:
            missing.extend([token] * delta)

    extra = []
    for token, count in actual_counts.items():
        delta = count - expected_counts[token]
        if delta > 0:
            extra.extend([token] * delta)

    matched = len(shared)
    precision = matched / len(actual_words) if actual_words else 0.0
    recall = matched / len(expected_words) if expected_words else 0.0

    return {
        "expected_normalized": expected_norm,
        "actual_normalized": actual_norm,
        "sequence_ratio": matcher.ratio(),
        "word_precision": precision,
        "word_recall": recall,
        "missing_words": missing[:50],
        "extra_words": extra[:50],
    }


def format_srt_timestamp(value: float) -> str:
    total_ms = max(int(round(value * 1000)), 0)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, ms = divmod(rem, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def write_srt(path: Path, segments: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        lines.extend(
            [
                str(index),
                f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
                text,
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    run_name = args.run_name or args.input.stem
    expected_text = args.expected_text.strip()
    if args.expected_text_file:
        expected_text = args.expected_text_file.read_text(encoding="utf-8").strip()

    json_path = args.out_dir / f"{run_name}.asr_qc.json"
    txt_path = args.out_dir / f"{run_name}.transcript.txt"
    srt_path = args.out_dir / f"{run_name}.transcript.srt"

    with tempfile.TemporaryDirectory(prefix="spoken-asr-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        wav_path = temp_dir / "audio.wav"
        extract_audio(args.input, wav_path)
        duration_seconds = run_ffprobe_duration(args.input)

        model = whisper.load_model(args.model)
        transcribe_kwargs: dict[str, Any] = {
            "language": args.language or None,
            "task": "transcribe",
            "verbose": False,
            "fp16": False,
        }
        if args.word_timestamps:
            transcribe_kwargs["word_timestamps"] = True
        try:
            result = model.transcribe(str(wav_path), **transcribe_kwargs)
        except TypeError:
            transcribe_kwargs.pop("word_timestamps", None)
            result = model.transcribe(str(wav_path), **transcribe_kwargs)

    transcript = str(result.get("text", "")).strip()
    txt_path.write_text(transcript + "\n", encoding="utf-8")
    segments = list(result.get("segments") or [])
    if segments:
        write_srt(srt_path, segments)

    comparison: dict[str, Any] | None = None
    status = "transcript_only"
    if expected_text:
        comparison = compare_text(expected_text, transcript)
        ratio = float(comparison["sequence_ratio"])
        if ratio >= args.pass_threshold:
            status = "pass"
        elif ratio >= args.warn_threshold:
            status = "warn"
        else:
            status = "fail"

    payload = {
        "input": str(args.input),
        "duration_seconds": duration_seconds,
        "model": args.model,
        "language": args.language,
        "word_timestamps_requested": args.word_timestamps,
        "transcript": transcript,
        "expected_text": expected_text,
        "comparison": comparison,
        "status": status,
        "segments": segments,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
