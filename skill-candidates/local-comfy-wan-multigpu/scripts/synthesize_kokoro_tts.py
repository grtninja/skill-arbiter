#!/usr/bin/env python
import argparse
import io
import json
import wave
from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro


def to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    samples = np.asarray(audio, dtype=np.float32)
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767.0).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(pcm.tobytes())
    return buffer.getvalue()


def apply_pitch_shift(audio: np.ndarray, semitones: float) -> np.ndarray:
    samples = np.asarray(audio, dtype=np.float32)
    if samples.size < 2 or abs(semitones) < 0.05:
        return samples
    ratio = float(np.clip(2.0 ** (semitones / 12.0), 0.5, 2.0))
    source_index = np.arange(samples.shape[0], dtype=np.float32)
    warped_length = max(2, int(round(samples.shape[0] / ratio)))
    warped_index = np.linspace(0, samples.shape[0] - 1, warped_length, dtype=np.float32)
    warped = np.interp(warped_index, source_index, samples)
    restored_index = np.linspace(0, warped.shape[0] - 1, samples.shape[0], dtype=np.float32)
    restored = np.interp(
        restored_index,
        np.arange(warped.shape[0], dtype=np.float32),
        warped,
    )
    return restored.astype(np.float32)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize local Kokoro speech for the Penny media loop.",
    )
    parser.add_argument("--model", required=True, help="Path to kokoro-v1.0.onnx")
    parser.add_argument("--voices", required=True, help="Path to voices-v1.0.bin")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--voice", default="af_jessica", help="Kokoro voice id")
    parser.add_argument("--text", help="Inline text to synthesize")
    parser.add_argument("--text-file", help="Path to a UTF-8 text file to synthesize")
    parser.add_argument("--lang", default="en-us", help="Speech language")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    parser.add_argument(
        "--pitch-shift",
        type=float,
        default=0.0,
        help="Semitone pitch shift to apply after synthesis",
    )
    parser.add_argument(
        "--meta-out",
        help="Optional JSON sidecar output with synthesis metadata",
    )
    return parser.parse_args()


def resolve_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    return str(args.text or "").strip()


def main() -> int:
    args = parse_args()
    text = resolve_text(args)
    if not text:
        raise SystemExit("text_required")

    model_path = Path(args.model)
    voices_path = Path(args.voices)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kokoro = Kokoro(str(model_path), str(voices_path))
    available_voices = sorted(list(kokoro.voices.keys()))
    voice = args.voice if args.voice in available_voices else "af_jessica"
    if voice not in available_voices:
        voice = available_voices[0]

    audio, sample_rate = kokoro.create(
        text,
        voice=voice,
        speed=float(args.speed),
        lang=str(args.lang).strip().lower().replace("_", "-"),
    )
    shifted_audio = apply_pitch_shift(audio, float(args.pitch_shift))
    output_path.write_bytes(to_wav_bytes(shifted_audio, sample_rate))

    if args.meta_out:
        meta_path = Path(args.meta_out)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(
                {
                    "voice": voice,
                    "requested_voice": args.voice,
                    "lang": args.lang,
                    "speed": float(args.speed),
                    "pitch_shift": float(args.pitch_shift),
                    "sample_rate": int(sample_rate),
                    "samples": int(np.asarray(shifted_audio).shape[0]),
                    "duration_seconds": round(
                        int(np.asarray(shifted_audio).shape[0]) / float(sample_rate), 6
                    ),
                    "model": str(model_path),
                    "voices": str(voices_path),
                    "output": str(output_path),
                    "text": text,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
