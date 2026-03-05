#!/usr/bin/env python3
"""Write a deterministic Blender fit checkpoint record."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a visible-fit checkpoint JSON")
    parser.add_argument("--scene", required=True, help="Path to .blend scene")
    parser.add_argument("--stage", required=True, help="Pipeline stage label")
    parser.add_argument("--notes", default="", help="Optional operator notes")
    parser.add_argument("--json-out", required=True, help="Output JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scene = Path(args.scene).expanduser().resolve()
    out = Path(args.json_out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scene": str(scene),
        "scene_exists": scene.exists(),
        "stage": args.stage.strip(),
        "notes": args.notes.strip(),
    }

    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
