#!/usr/bin/env python3
"""Scan local VRoid/AvatarMaker template assets and write a manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

_home = Path(os.environ.get("USERPROFILE", str(Path.home()))).expanduser()
SEARCH_ROOTS = [
    _home / "AppData" / "LocalLow" / "YiMeta" / "VRoid Clothing Maker",
    _home / "Downloads" / "VRM AVATAR STUFF",
]

KEYWORDS = {
    "dress": ["cheong", "dress", "tops", "o_f_", "cloth"],
    "shoes": ["shoes", "s_f_", "heel"],
    "body": ["b_f_", "body", "template"],
}

EXTS = {".png", ".jpg", ".jpeg", ".zip", ".vrm"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan VRoid template assets")
    parser.add_argument("--mirror-root", default="", help="Optional destination to mirror detected files")
    parser.add_argument("--json-out", required=True, help="Manifest output JSON path")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(name: str) -> set[str]:
    lowered = name.lower()
    tags = set()
    for tag, needles in KEYWORDS.items():
        if any(n in lowered for n in needles):
            tags.add(tag)
    return tags


def main() -> None:
    args = parse_args()
    mirror_root = Path(args.mirror_root).expanduser().resolve() if args.mirror_root else None
    if mirror_root:
        mirror_root.mkdir(parents=True, exist_ok=True)

    files = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in EXTS:
                tags = sorted(classify(p.name))
                if not tags:
                    continue
                entry = {
                    "path": str(p.resolve()),
                    "name": p.name,
                    "size": p.stat().st_size,
                    "sha256": sha256_file(p),
                    "tags": tags,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
                }
                files.append(entry)
                if mirror_root:
                    target = mirror_root / p.name
                    if not target.exists():
                        copy2(p, target)

    required = {"body", "dress", "shoes"}
    seen = {tag for f in files for tag in f["tags"]}
    missing = sorted(required - seen)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roots": [str(r) for r in SEARCH_ROOTS],
        "count": len(files),
        "missing_required_tags": missing,
        "complete": len(missing) == 0,
        "files": files,
    }

    out = Path(args.json_out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"count": payload["count"], "complete": payload["complete"], "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
