#!/usr/bin/env python3
"""Inspect live Comfy Wan node inputs to discover practical clip settings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Wan node input schema from a live Comfy server")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Comfy base URL")
    parser.add_argument("--node", default="WanImageToVideo", help="Node name to inspect")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with urlopen(f"{args.base_url}/object_info/{args.node}") as response:
        payload = json.load(response)
    node = payload.get(args.node, {})
    summary = {
        "node": args.node,
        "input": node.get("input", {}),
        "input_order": node.get("input_order", {}),
        "output": node.get("output", []),
        "output_is_list": node.get("output_is_list", []),
        "name": node.get("name"),
        "display_name": node.get("display_name"),
        "description": node.get("description"),
        "category": node.get("category"),
    }
    text = json.dumps(summary, indent=2)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
