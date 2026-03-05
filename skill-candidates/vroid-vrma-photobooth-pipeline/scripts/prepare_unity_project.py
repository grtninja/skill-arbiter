#!/usr/bin/env python3
"""Prepare an AssetRipper Unity export for VRoid Photo Booth VRMA batch export."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Unity project for VRMA export")
    parser.add_argument("--unity-project", required=True, help="Path to AssetRipper ExportedProject")
    parser.add_argument("--univrm-root", required=True, help="Path to UniVRM root (contains Assets/UniGLTF and Assets/VRM10)")
    parser.add_argument(
        "--exporter-template",
        default="",
        help="Optional path to VroidVrmaBatch.cs template (defaults to skill assets)",
    )
    parser.add_argument(
        "--skip-disable-assetripper-scripts",
        action="store_true",
        help="Skip moving ExportedProject/Assets/Scripts out of compile path",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON report output")
    return parser.parse_args()


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.name}_{stamp}")


def move_dir_if_exists(source: Path, destination: Path) -> str:
    if not source.exists():
        return ""
    final_destination = unique_destination(destination)
    final_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(final_destination))
    return str(final_destination)


def to_file_uri(path: Path) -> str:
    return "file:" + path.resolve().as_posix()


def patch_manifest(manifest_path: Path, univrm_root: Path) -> dict[str, str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    dependencies = data.setdefault("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ValueError("manifest.json dependencies must be an object")

    gltf_path = univrm_root / "Assets" / "UniGLTF"
    vrm10_path = univrm_root / "Assets" / "VRM10"
    if not gltf_path.is_dir():
        raise FileNotFoundError(f"Missing UniGLTF package path: {gltf_path}")
    if not vrm10_path.is_dir():
        raise FileNotFoundError(f"Missing VRM10 package path: {vrm10_path}")

    dependencies["com.vrmc.gltf"] = to_file_uri(gltf_path)
    dependencies["com.vrmc.vrm"] = to_file_uri(vrm10_path)

    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {
        "com.vrmc.gltf": dependencies["com.vrmc.gltf"],
        "com.vrmc.vrm": dependencies["com.vrmc.vrm"],
    }


def install_exporter(template_path: Path, unity_project: Path) -> str:
    if not template_path.is_file():
        raise FileNotFoundError(f"Exporter template not found: {template_path}")

    editor_dir = unity_project / "Assets" / "Editor"
    editor_dir.mkdir(parents=True, exist_ok=True)
    destination = editor_dir / "VroidVrmaBatch.cs"
    shutil.copyfile(str(template_path), str(destination))
    return str(destination)


def main() -> int:
    args = parse_args()

    unity_project = Path(args.unity_project).expanduser().resolve()
    univrm_root = Path(args.univrm_root).expanduser().resolve()

    if not unity_project.is_dir():
        print(f"error: unity project not found: {unity_project}", file=sys.stderr)
        return 2
    if not univrm_root.is_dir():
        print(f"error: univrm root not found: {univrm_root}", file=sys.stderr)
        return 2

    manifest_path = unity_project / "Packages" / "manifest.json"
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    script_root = Path(__file__).resolve().parent
    default_template = script_root.parent / "assets" / "VroidVrmaBatch.cs"
    template_path = Path(args.exporter_template).expanduser().resolve() if args.exporter_template else default_template

    report: dict[str, Any] = {
        "unity_project": str(unity_project),
        "univrm_root": str(univrm_root),
        "moved_assetripper_scripts_to": "",
        "moved_unigltf_testrunner_to": "",
        "manifest_dependencies": {},
        "installed_exporter": "",
    }

    try:
        if not args.skip_disable_assetripper_scripts:
            source_scripts = unity_project / "Assets" / "Scripts"
            destination_scripts = unity_project / "_disabled_Scripts_from_assetripper"
            report["moved_assetripper_scripts_to"] = move_dir_if_exists(source_scripts, destination_scripts)

        test_runner = univrm_root / "Assets" / "UniGLTF" / "Editor" / "TestRunner"
        disabled_test_runner = univrm_root / "_disabled_UniGLTF_TestRunner"
        report["moved_unigltf_testrunner_to"] = move_dir_if_exists(test_runner, disabled_test_runner)

        report["manifest_dependencies"] = patch_manifest(manifest_path, univrm_root)
        report["installed_exporter"] = install_exporter(template_path, unity_project)
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        report["error"] = str(exc)
        write_json(args.json_out, report)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_json(args.json_out, report)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
