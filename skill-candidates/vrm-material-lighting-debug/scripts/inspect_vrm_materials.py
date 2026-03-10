#!/usr/bin/env python3
"""
Inspect VRM/GLB material settings with emphasis on VRMC_materials_mtoon fields.

This is intended for live VRM Sandbox debugging where clothing shades differently
from skin/legs or appears to have inverted-looking shadows.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path


JSON_CHUNK_TYPE = 0x4E4F534A


def read_glb_json(vrm_path: Path) -> dict:
    data = vrm_path.read_bytes()
    if len(data) < 20:
        raise ValueError("file is too small to be a valid glb/vrm")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError("file is not a valid glb/vrm")
    if length > len(data):
        raise ValueError("declared glb length exceeds file size")

    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk_data = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == JSON_CHUNK_TYPE:
            return json.loads(chunk_data.decode("utf-8"))

    raise ValueError("glb json chunk not found")


def build_material_usage(doc: dict) -> dict[int, list[str]]:
    usage: dict[int, list[str]] = {}
    meshes = doc.get("meshes", [])
    for mesh_index, mesh in enumerate(meshes):
        mesh_name = mesh.get("name") or f"mesh_{mesh_index}"
        for prim_index, primitive in enumerate(mesh.get("primitives", [])):
            material_index = primitive.get("material")
            if material_index is None:
                continue
            usage.setdefault(material_index, []).append(f"{mesh_name}[{prim_index}]")
    return usage


def summarize_material(index: int, material: dict, usage: dict[int, list[str]]) -> dict:
    extensions = material.get("extensions", {})
    mtoon = extensions.get("VRMC_materials_mtoon", {})
    pbr = material.get("pbrMetallicRoughness", {})
    return {
        "index": index,
        "name": material.get("name") or f"material_{index}",
        "doubleSided": material.get("doubleSided", False),
        "alphaMode": material.get("alphaMode", "OPAQUE"),
        "baseColorFactor": pbr.get("baseColorFactor"),
        "shadeColorFactor": mtoon.get("shadeColorFactor"),
        "giEqualizationFactor": mtoon.get("giEqualizationFactor"),
        "matcapFactor": mtoon.get("matcapFactor"),
        "rimLightingMixFactor": mtoon.get("rimLightingMixFactor"),
        "parametricRimLiftFactor": mtoon.get("parametricRimLiftFactor"),
        "parametricRimColorFactor": mtoon.get("parametricRimColorFactor"),
        "shadingToonyFactor": mtoon.get("shadingToonyFactor"),
        "shadingShiftFactor": mtoon.get("shadingShiftFactor"),
        "outlineWidthFactor": mtoon.get("outlineWidthFactor"),
        "usage": usage.get(index, []),
    }


def filter_materials(materials: list[dict], pattern: str | None) -> list[dict]:
    if not pattern:
        return materials
    regex = re.compile(pattern, re.IGNORECASE)
    return [item for item in materials if regex.search(item["name"])]


def print_summary(vrm_path: Path, materials: list[dict]) -> None:
    print(f"VRM: {vrm_path}")
    print(f"Materials matched: {len(materials)}")
    for item in materials:
        print()
        print(f"[{item['index']}] {item['name']}")
        if item["usage"]:
            print(f"  usage: {', '.join(item['usage'])}")
        print(f"  doubleSided: {item['doubleSided']}")
        print(f"  alphaMode: {item['alphaMode']}")
        for key in (
            "baseColorFactor",
            "shadeColorFactor",
            "giEqualizationFactor",
            "matcapFactor",
            "rimLightingMixFactor",
            "parametricRimLiftFactor",
            "parametricRimColorFactor",
            "shadingToonyFactor",
            "shadingShiftFactor",
            "outlineWidthFactor",
        ):
            value = item.get(key)
            if value is not None:
                print(f"  {key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vrm", required=True, help="Path to the .vrm/.glb file")
    parser.add_argument(
        "--name-filter",
        help="Regex used to keep only matching material names",
    )
    parser.add_argument("--json-out", help="Optional path for structured JSON output")
    args = parser.parse_args()

    vrm_path = Path(args.vrm).expanduser().resolve()
    if not vrm_path.exists():
        print(f"[ERROR] VRM file not found: {vrm_path}", file=sys.stderr)
        return 1

    try:
        doc = read_glb_json(vrm_path)
    except Exception as exc:  # pragma: no cover - defensive CLI reporting
        print(f"[ERROR] Failed to read VRM: {exc}", file=sys.stderr)
        return 1

    usage = build_material_usage(doc)
    materials = [
        summarize_material(index, material, usage)
        for index, material in enumerate(doc.get("materials", []))
    ]
    materials = filter_materials(materials, args.name_filter)

    payload = {
        "vrm": str(vrm_path),
        "matched_materials": materials,
        "matched_count": len(materials),
    }

    print_summary(vrm_path, materials)

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print()
        print(f"Wrote JSON: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
