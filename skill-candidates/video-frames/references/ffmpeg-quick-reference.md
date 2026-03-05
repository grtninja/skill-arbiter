# ffmpeg Quick Reference

Common commands used by `video-frames`:

## Extract a single frame at timestamp

```bash
ffmpeg -hide_banner -loglevel error -y -ss 00:00:12 -i input.mp4 -frames:v 1 frame.jpg
```

## Extract a frame by index

```bash
ffmpeg -hide_banner -loglevel error -y -i input.mp4 -vf "select=eq(n\,42)" -vframes 1 frame.png
```

## Extract a short clip

```bash
ffmpeg -hide_banner -loglevel error -y -ss 00:00:10 -i input.mp4 -t 5 clip.mp4
```
