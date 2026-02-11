#!/usr/bin/env python3
"""Validate Comfy/AMUSE/CapCut media pipeline contracts on local shim endpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Comfy media pipeline contract")
    parser.add_argument("--base-url", default="http://127.0.0.1:9000", help="Shim base URL")
    parser.add_argument(
        "--require-profile",
        action="append",
        default=[],
        help="Required /api/comfy/pipelines/profiles profile name (repeatable)",
    )
    parser.add_argument(
        "--require-capcut",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require capcut_export metadata in required profiles",
    )
    parser.add_argument(
        "--require-amuse",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Require /api/amuse/status to report enabled+reachable",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def fetch_json(base_url: str, path: str, timeout_s: float) -> tuple[bool, int, dict[str, Any], str]:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310
            status = int(getattr(resp, "status", 0) or 0)
            raw = resp.read().decode("utf-8", errors="replace")
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return False, status, {}, "response payload is not an object"
        return True, status, payload, ""
    except urllib.error.HTTPError as exc:
        return False, int(exc.code or 0), {}, f"http error: {exc}"
    except urllib.error.URLError as exc:
        return False, 0, {}, f"url error: {exc}"
    except json.JSONDecodeError as exc:
        return False, 0, {}, f"json decode error: {exc}"


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    required_profiles = [text.strip() for text in args.require_profile if text.strip()]

    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    ok, status, mcp_payload, error = fetch_json(args.base_url, "/api/mcp/status", args.timeout_seconds)
    checks.append({"path": "/api/mcp/status", "ok": ok, "status": status, "error": error})
    if not ok:
        failures.append("mcp_status_unreachable")
    else:
        if not bool(mcp_payload.get("enabled")):
            failures.append("mcp_not_enabled")
        if not bool(mcp_payload.get("running")):
            failures.append("mcp_not_running")
        tools = set(mcp_payload.get("tools") or [])
        resources = set(mcp_payload.get("resources") or [])
        for tool in ("shim.comfy.workflow.submit", "shim.comfy.pipeline.run"):
            if tool not in tools:
                failures.append(f"missing_tool:{tool}")
        for res in ("shim.comfy.status", "shim.comfy.queue", "shim.comfy.history"):
            if res not in resources:
                failures.append(f"missing_resource:{res}")

    ok, status, profiles_payload, error = fetch_json(
        args.base_url,
        "/api/comfy/pipelines/profiles",
        args.timeout_seconds,
    )
    checks.append({"path": "/api/comfy/pipelines/profiles", "ok": ok, "status": status, "error": error})
    profile_rows: dict[str, dict[str, Any]] = {}
    default_profile = ""
    if not ok:
        failures.append("pipeline_profiles_unreachable")
    else:
        default_profile = str(profiles_payload.get("default_profile") or "").strip()
        rows = profiles_payload.get("profiles")
        if not isinstance(rows, list):
            failures.append("pipeline_profiles_invalid")
        else:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                name = str(row.get("profile") or "").strip()
                if name:
                    profile_rows[name] = row

            for profile in required_profiles:
                if profile not in profile_rows:
                    failures.append(f"missing_profile:{profile}")
                elif args.require_capcut:
                    capcut = profile_rows[profile].get("capcut_export")
                    if not isinstance(capcut, dict):
                        failures.append(f"missing_capcut_export:{profile}")
                    elif str(capcut.get("editor") or "").strip().lower() != "capcut":
                        failures.append(f"invalid_capcut_editor:{profile}")

    amuse_enabled = False
    amuse_reachable = False
    ok, status, amuse_payload, error = fetch_json(args.base_url, "/api/amuse/status", args.timeout_seconds)
    checks.append({"path": "/api/amuse/status", "ok": ok, "status": status, "error": error})
    if ok:
        amuse_enabled = bool(amuse_payload.get("enabled"))
        amuse_reachable = bool(amuse_payload.get("reachable"))
    elif args.require_amuse:
        failures.append("amuse_status_unreachable")

    if args.require_amuse:
        if not amuse_enabled:
            failures.append("amuse_not_enabled")
        if not amuse_reachable:
            failures.append("amuse_not_reachable")

    payload: dict[str, Any] = {
        "base_url": args.base_url,
        "required_profiles": required_profiles,
        "default_profile": default_profile,
        "require_capcut": bool(args.require_capcut),
        "require_amuse": bool(args.require_amuse),
        "checks": checks,
        "profiles_found": sorted(profile_rows.keys()),
        "amuse_enabled": amuse_enabled,
        "amuse_reachable": amuse_reachable,
        "failures": failures,
        "ok": not failures,
    }

    write_json(args.json_out, payload)

    print("media_pipeline_check: " + ("pass" if payload["ok"] else "fail"))
    print(f"profiles_found={len(profile_rows)} default_profile={default_profile or 'unknown'}")
    if failures:
        for item in failures:
            print(f"failure:{item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
