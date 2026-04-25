---
name: "video-frames"
author: "grtninja"
canonical_source: "https://github.com/grtninja/skill-arbiter"
description: "Extract frames and short clips from local video files with ffmpeg. Use when you need quick visual checkpoints without opening a full editor."
---

# Video Frames

Use this skill to pull exact frames or short clips from a local video.

## Workflow

1. Confirm `ffmpeg` is installed and the input file exists.
2. Extract one frame by timestamp or by frame index.
3. Optionally export a short clip for review context.
4. Keep outputs in a deterministic artifact folder for repeatable checks.

## Frame Extraction

```bash
python3 "$CODEX_HOME/skills/video-frames/scripts/video_frames.py" frame \
  --input /path/to/video.mp4 \
  --time 00:00:12 \
  --out /tmp/frame-12s.jpg
```

By frame index:

```bash
python3 "$CODEX_HOME/skills/video-frames/scripts/video_frames.py" frame \
  --input /path/to/video.mp4 \
  --index 0 \
  --out /tmp/frame-0.png
```

## Short Clip Export

```bash
python3 "$CODEX_HOME/skills/video-frames/scripts/video_frames.py" clip \
  --input /path/to/video.mp4 \
  --start 00:00:10 \
  --duration 5 \
  --out /tmp/clip-10s-15s.mp4
```

## Guardrails

- Local files only; do not fetch remote media in this lane.
- Keep extraction deterministic (`--time` or `--index` must be explicit in reviews).
- Preserve source files; write only to target output paths.

## Scope Boundary

Use this skill only for frame/clip extraction and lightweight visual inspection.

Do not use this skill as a replacement for full timeline editing or compositing.

## References

- `references/ffmpeg-quick-reference.md`
