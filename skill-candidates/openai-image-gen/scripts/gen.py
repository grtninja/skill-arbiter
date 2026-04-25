#!/usr/bin/env python3
import argparse
import base64
import datetime as dt
import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from html import escape as html_escape
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "image"


def default_out_dir() -> Path:
    now = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    preferred = Path.home() / "Projects" / "tmp"
    base = preferred if preferred.is_dir() else Path("./tmp")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"openai-image-gen-{now}"


def pick_prompts(count: int) -> list[str]:
    subjects = [
        "a lobster astronaut",
        "a brutalist lighthouse",
        "a cozy reading nook",
        "a cyberpunk noodle shop",
        "a Vienna street at dusk",
        "a minimalist product photo",
        "a surreal underwater library",
    ]
    styles = [
        "ultra-detailed studio photo",
        "35mm film still",
        "isometric illustration",
        "editorial photography",
        "soft watercolor",
        "architectural render",
        "high-contrast monochrome",
    ]
    lighting = [
        "golden hour",
        "overcast soft light",
        "neon lighting",
        "dramatic rim light",
        "candlelight",
        "foggy atmosphere",
    ]
    prompts: list[str] = []
    for _ in range(count):
        prompts.append(
            f"{random.choice(styles)} of {random.choice(subjects)}, {random.choice(lighting)}"
        )
    return prompts


def is_gpt_image_2(model: str) -> bool:
    return model == "gpt-image-2" or model.startswith("gpt-image-2-")


def get_model_defaults(model: str) -> tuple[str, str]:
    """Return (default_size, default_quality) for the given model."""
    if model == "dall-e-2":
        # quality will be ignored
        return ("1024x1024", "standard")
    elif model == "dall-e-3":
        return ("1024x1024", "standard")
    elif is_gpt_image_2(model):
        return ("auto", "auto")
    else:
        # Older GPT Image models keep the previous deterministic defaults.
        return ("1024x1024", "high")


def validate_gpt_image_2_size(size: str) -> None:
    if size == "auto":
        return

    match = re.fullmatch(r"(\d+)x(\d+)", size)
    if not match:
        raise ValueError("gpt-image-2 size must be 'auto' or '<width>x<height>'")

    width = int(match.group(1))
    height = int(match.group(2))
    long_edge = max(width, height)
    short_edge = min(width, height)
    pixels = width * height

    if width % 16 or height % 16:
        raise ValueError("gpt-image-2 size edges must be multiples of 16")
    if long_edge > 3840:
        raise ValueError("gpt-image-2 size edge must be <= 3840px")
    if long_edge / short_edge > 3:
        raise ValueError("gpt-image-2 size ratio must not exceed 3:1")
    if pixels < 655_360 or pixels > 8_294_400:
        raise ValueError("gpt-image-2 total pixels must be between 655,360 and 8,294,400")


def validate_model_options(
    model: str,
    size: str,
    quality: str,
    background: str,
    output_format: str,
    output_compression: int | None,
    style: str,
) -> None:
    if is_gpt_image_2(model):
        validate_gpt_image_2_size(size)
        if background == "transparent":
            raise ValueError("gpt-image-2 does not support background=transparent")
        if quality not in {"auto", "low", "medium", "high"}:
            raise ValueError("gpt-image-2 quality must be auto, low, medium, or high")

    if output_format and output_format not in {"png", "jpeg", "webp"}:
        raise ValueError("--output-format must be png, jpeg, or webp")
    if output_compression is not None:
        if output_format not in {"jpeg", "webp"}:
            raise ValueError("--output-compression requires --output-format jpeg or webp")
        if not 0 <= output_compression <= 100:
            raise ValueError("--output-compression must be between 0 and 100")
    if style and model != "dall-e-3":
        raise ValueError("--style is only supported by dall-e-3")


def output_file_ext(model: str, output_format: str) -> str:
    if model.startswith("gpt-image") and output_format:
        return output_format
    return "png"


def request_images(
    api_key: str,
    prompt: str,
    model: str,
    size: str,
    quality: str,
    background: str = "",
    output_format: str = "",
    output_compression: int | None = None,
    style: str = "",
    timeout: int = 300,
) -> dict:
    url = "https://api.openai.com/v1/images/generations"
    args = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }

    # Quality parameter - dall-e-2 doesn't accept this parameter
    if model != "dall-e-2":
        args["quality"] = quality

    # Note: response_format no longer supported by OpenAI Images API
    # dall-e models now return URLs by default

    if model.startswith("gpt-image"):
        if background:
            args["background"] = background
        if output_format:
            args["output_format"] = output_format
        if output_compression is not None:
            args["output_compression"] = output_compression

    if model == "dall-e-3" and style:
        args["style"] = style

    body = json.dumps(args).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=body,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Images API failed ({e.code}): {payload}") from e


def write_gallery(out_dir: Path, items: list[dict]) -> None:
    thumbs = "\n".join(
        [
            f"""
<figure>
  <a href="{html_escape(it["file"], quote=True)}"><img src="{html_escape(it["file"], quote=True)}" loading="lazy" /></a>
  <figcaption>{html_escape(it["prompt"])}</figcaption>
</figure>
""".strip()
            for it in items
        ]
    )
    html = f"""<!doctype html>
<meta charset="utf-8" />
<title>openai-image-gen</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 24px; font: 14px/1.4 ui-sans-serif, system-ui; background: #0b0f14; color: #e8edf2; }}
  h1 {{ font-size: 18px; margin: 0 0 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
  figure {{ margin: 0; padding: 12px; border: 1px solid #1e2a36; border-radius: 14px; background: #0f1620; }}
  img {{ width: 100%; height: auto; border-radius: 10px; display: block; }}
  figcaption {{ margin-top: 10px; color: #b7c2cc; }}
  code {{ color: #9cd1ff; }}
</style>
<h1>openai-image-gen</h1>
<p>Output: <code>{html_escape(out_dir.as_posix())}</code></p>
<div class="grid">
{thumbs}
</div>
"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate images via OpenAI Images API.")
    ap.add_argument("--prompt", help="Single prompt. If omitted, random prompts are generated.")
    ap.add_argument("--count", type=int, default=8, help="How many images to generate.")
    ap.add_argument("--model", default="gpt-image-2", help="Image model id.")
    ap.add_argument("--size", default="", help="Image size (e.g. 1024x1024, 1536x1024). Defaults based on model if not specified.")
    ap.add_argument("--quality", default="", help="Image quality (e.g. high, standard). Defaults based on model if not specified.")
    ap.add_argument("--background", default="", help="Background option for GPT models: opaque or auto for gpt-image-2; transparent only for older models that support it.")
    ap.add_argument("--output-format", default="", help="Output format (GPT models only): png, jpeg, or webp.")
    ap.add_argument("--output-compression", type=int, help="JPEG/WebP compression level from 0 to 100 (GPT Image models only).")
    ap.add_argument("--style", default="", help="Image style (dall-e-3 only): vivid or natural.")
    ap.add_argument("--timeout", type=int, default=300, help="HTTP timeout in seconds. GPT Image prompts can take up to 2 minutes.")
    ap.add_argument("--out-dir", default="", help="Output directory (default: ./tmp/openai-image-gen-<ts>).")
    args = ap.parse_args()

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("Missing OPENAI_API_KEY", file=sys.stderr)
        return 2

    # Apply model-specific defaults if not specified
    default_size, default_quality = get_model_defaults(args.model)
    size = args.size or default_size
    quality = args.quality or default_quality
    try:
        validate_model_options(
            args.model,
            size,
            quality,
            args.background,
            args.output_format,
            args.output_compression,
            args.style,
        )
    except ValueError as exc:
        print(f"Invalid image generation options: {exc}", file=sys.stderr)
        return 2

    count = args.count
    if args.model == "dall-e-3" and count > 1:
        print(f"Warning: dall-e-3 only supports generating 1 image at a time. Reducing count from {count} to 1.", file=sys.stderr)
        count = 1

    out_dir = Path(args.out_dir).expanduser() if args.out_dir else default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts = [args.prompt] * count if args.prompt else pick_prompts(count)

    # Determine file extension based on output format
    file_ext = output_file_ext(args.model, args.output_format)

    items: list[dict] = []
    for idx, prompt in enumerate(prompts, start=1):
        print(f"[{idx}/{len(prompts)}] {prompt}")
        res = request_images(
            api_key,
            prompt,
            args.model,
            size,
            quality,
            args.background,
            args.output_format,
            args.output_compression,
            args.style,
            args.timeout,
        )
        data = res.get("data", [{}])[0]
        image_b64 = data.get("b64_json")
        image_url = data.get("url")
        if not image_b64 and not image_url:
            raise RuntimeError(f"Unexpected response: {json.dumps(res)[:400]}")

        filename = f"{idx:03d}-{slugify(prompt)[:40]}.{file_ext}"
        filepath = out_dir / filename
        if image_b64:
            filepath.write_bytes(base64.b64decode(image_b64))
        else:
            try:
                urllib.request.urlretrieve(image_url, filepath)
            except urllib.error.URLError as e:
                raise RuntimeError(f"Failed to download image from {image_url}: {e}") from e

        items.append({"prompt": prompt, "file": filename})

    (out_dir / "prompts.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    write_gallery(out_dir, items)
    print(f"\nWrote: {(out_dir / 'index.html').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
