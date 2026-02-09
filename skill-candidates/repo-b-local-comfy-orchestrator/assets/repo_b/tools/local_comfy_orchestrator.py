#!/usr/bin/env python3
"""Manual local Comfy MCP resource orchestrator with fail-closed policy."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

try:
    from local_comfy_validate import validate_comfy_resources
except ImportError as exc:
    validate_comfy_resources = None
    VALIDATOR_IMPORT_ERROR = str(exc)
else:
    VALIDATOR_IMPORT_ERROR = ""

EXIT_SUCCESS = 0
EXIT_MCP_UNAVAILABLE = 10
EXIT_RESOURCE_UNAVAILABLE = 11
EXIT_VALIDATION_FAILED = 12
EXIT_POLICY_VIOLATION = 13

DEFAULT_BASE_URL = "http://127.0.0.1:9000"
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_STATUS_MAX_AGE_SECONDS = 60
DEFAULT_MAX_HINTS = 12

REQUIRED_RESOURCES = (
    "shim.comfy.status",
    "shim.comfy.queue",
    "shim.comfy.history",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local Comfy MCP orchestration in fail-closed mode")
    parser.add_argument("--task", required=True, help="Task identifier")
    parser.add_argument("--json-out", required=True, help="Output JSON report path")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="REST base URL for MCP status probe")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="REST/MCP timeout")
    return parser.parse_args()


def _env_enabled(value: str | None, default: bool = True) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _is_loopback_host(host: str) -> bool:
    candidate = str(host or "").strip()
    if not candidate:
        return False
    if candidate.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _request_json(method: str, url: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(url=url, method=method, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
            payload = json.loads(raw) if raw else {}
            return {
                "ok": True,
                "status": int(getattr(response, "status", 200)),
                "payload": payload,
                "error": "",
            }
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "status": 0,
            "payload": {},
            "error": f"invalid_json:{str(exc)}",
        }
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace").strip()
        except OSError:
            detail = ""
        return {
            "ok": False,
            "status": int(exc.code),
            "payload": {},
            "error": f"http_error:{exc.code}:{detail[:180]}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "status": 0,
            "payload": {},
            "error": f"transport_error:{str(getattr(exc, 'reason', exc))}",
        }


def get_mcp_status(base_url: str, timeout_seconds: float) -> dict[str, Any]:
    return _request_json("GET", f"{base_url.rstrip('/')}/api/mcp/status", timeout_seconds)


def _jsonrpc_call(
    reader: Any,
    writer: Any,
    request_id: int,
    method: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = dict(params)

    writer.write(json.dumps(payload, separators=(",", ":")) + "\n")
    writer.flush()

    line = reader.readline()
    if not line:
        raise RuntimeError("empty response from MCP adapter")
    parsed = json.loads(line.strip())
    if not isinstance(parsed, dict):
        raise ValueError("MCP response must be an object")
    if "error" in parsed:
        error_payload = parsed.get("error")
        if isinstance(error_payload, dict):
            message = str(error_payload.get("message") or "unknown MCP error")
        else:
            message = "unknown MCP error"
        raise RuntimeError(message)
    return parsed


def _normalize_resource_contents(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            if isinstance(first.get("json"), dict):
                return first["json"]
            text_value = first.get("text")
            if isinstance(text_value, str):
                try:
                    parsed = json.loads(text_value)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None


def read_comfy_resources(host: str, port: int, timeout_seconds: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "initialize_ok": False,
        "resources_list_ok": False,
        "available_resources": [],
        "reads": {},
        "error": "",
    }

    try:
        with socket.create_connection((host, int(port)), timeout=timeout_seconds) as sock:
            sock.settimeout(timeout_seconds)
            with (
                sock.makefile("r", encoding="utf-8", newline="\n") as reader,
                sock.makefile("w", encoding="utf-8", newline="\n") as writer,
            ):
                _jsonrpc_call(reader, writer, 1, "initialize")
                result["initialize_ok"] = True

                list_response = _jsonrpc_call(reader, writer, 2, "resources/list")
                result["resources_list_ok"] = True
                listed = list_response.get("result", {}).get("resources", [])
                if isinstance(listed, list):
                    uris = [str(item.get("uri", "")).strip() for item in listed if isinstance(item, dict)]
                    result["available_resources"] = sorted({uri for uri in uris if uri})

                for index, uri in enumerate(REQUIRED_RESOURCES, start=10):
                    if uri not in result["available_resources"]:
                        result["reads"][uri] = {
                            "ok": False,
                            "error": "resource not listed",
                            "payload": None,
                        }
                        continue
                    response = _jsonrpc_call(reader, writer, index, "resources/read", {"uri": uri})
                    contents = response.get("result", {}).get("contents")
                    normalized = _normalize_resource_contents(contents)
                    read_ok = isinstance(normalized, dict)
                    result["reads"][uri] = {
                        "ok": read_ok,
                        "error": "" if read_ok else "invalid resource contents",
                        "payload": normalized if read_ok else None,
                    }

        required_ok = all(result["reads"].get(uri, {}).get("ok") for uri in REQUIRED_RESOURCES)
        result["ok"] = bool(result["initialize_ok"] and result["resources_list_ok"] and required_ok)
        if not result["ok"] and not result["error"]:
            result["error"] = "required resource read failed"
        return result
    except Exception as exc:  # noqa: BLE001
        result["ok"] = False
        result["error"] = str(exc)
        return result


def _output_template(task_id: str) -> dict[str, Any]:
    return {
        "status": "unknown",
        "task_id": task_id,
        "mcp_probe": {"ok": False},
        "resource_probe": {
            "ok": False,
            "initialize_ok": False,
            "resources_list_ok": False,
            "available_resources": [],
            "reads": {},
            "error": "",
        },
        "validation": {
            "status": "not_run",
            "reason_codes": [],
            "cloud_fallback_count": 0,
        },
        "guidance_hints": [],
        "timing_ms": 0,
        "reason_codes": [],
        "cloud_fallback_count": 0,
    }


def _finalize(payload: dict[str, Any], started_mono: float) -> dict[str, Any]:
    payload["reason_codes"] = _dedupe(payload.get("reason_codes", []))
    payload["timing_ms"] = int((time.monotonic() - started_mono) * 1000)
    payload["cloud_fallback_count"] = 0
    validation = payload.get("validation")
    if isinstance(validation, dict):
        validation["cloud_fallback_count"] = 0
    return payload


def _policy_settings(environ: dict[str, str]) -> dict[str, Any]:
    reasons: list[str] = []
    enabled = _env_enabled(environ.get("REPO_B_LOCAL_COMFY_ORCH_ENABLED"), default=True)
    fail_closed = _env_enabled(environ.get("REPO_B_LOCAL_COMFY_ORCH_FAIL_CLOSED"), default=True)

    if not enabled:
        reasons.append("policy_violation")
    if not fail_closed:
        reasons.append("policy_violation")

    return {
        "ok": not reasons,
        "reason_codes": _dedupe(reasons),
        "status_max_age_seconds": max(
            _env_int(environ.get("REPO_B_LOCAL_COMFY_ORCH_STATUS_MAX_AGE_SECONDS"), DEFAULT_STATUS_MAX_AGE_SECONDS),
            1,
        ),
        "max_hints": max(
            _env_int(environ.get("REPO_B_LOCAL_COMFY_ORCH_MAX_HINTS"), DEFAULT_MAX_HINTS),
            1,
        ),
    }


def run(args: argparse.Namespace, environ: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    started_mono = time.monotonic()
    payload = _output_template(args.task)
    env = dict(os.environ if environ is None else environ)

    settings = _policy_settings(env)
    if not settings["ok"]:
        payload["status"] = "policy_violation"
        payload["reason_codes"].extend(settings["reason_codes"])
        return EXIT_POLICY_VIOLATION, _finalize(payload, started_mono)

    if validate_comfy_resources is None:
        payload["status"] = "policy_violation"
        payload["reason_codes"].append("policy_violation")
        payload["validation"] = {
            "status": "validator_unavailable",
            "reason_codes": ["policy_violation"],
            "detail": VALIDATOR_IMPORT_ERROR,
            "cloud_fallback_count": 0,
        }
        return EXIT_POLICY_VIOLATION, _finalize(payload, started_mono)

    base_url_override = str(env.get("REPO_B_LOCAL_COMFY_ORCH_BASE_URL") or "").strip()
    base_url = args.base_url
    if base_url_override and base_url == DEFAULT_BASE_URL:
        base_url = base_url_override

    mcp_status = get_mcp_status(base_url, args.timeout_seconds)
    payload["mcp_probe"] = {
        "ok": mcp_status["ok"],
        "status": mcp_status.get("status", 0),
        "error": mcp_status.get("error", ""),
        "payload": mcp_status.get("payload", {}),
        "base_url": base_url,
    }

    if not mcp_status["ok"]:
        payload["status"] = "mcp_unavailable"
        payload["reason_codes"].append("mcp_unavailable")
        return EXIT_MCP_UNAVAILABLE, _finalize(payload, started_mono)

    status_payload = mcp_status.get("payload")
    if not isinstance(status_payload, dict):
        payload["status"] = "mcp_unavailable"
        payload["reason_codes"].append("mcp_unavailable")
        return EXIT_MCP_UNAVAILABLE, _finalize(payload, started_mono)

    mcp_enabled = status_payload.get("enabled") is True
    mcp_running = status_payload.get("running") is True
    host = str(status_payload.get("host") or "").strip()
    port_value = status_payload.get("port")

    if not _is_loopback_host(host):
        payload["status"] = "policy_violation"
        payload["reason_codes"].append("policy_violation")
        return EXIT_POLICY_VIOLATION, _finalize(payload, started_mono)

    try:
        port = int(port_value)
    except (TypeError, ValueError):
        payload["status"] = "mcp_unavailable"
        payload["reason_codes"].append("mcp_unavailable")
        return EXIT_MCP_UNAVAILABLE, _finalize(payload, started_mono)

    if not mcp_enabled or not mcp_running:
        payload["status"] = "mcp_unavailable"
        payload["reason_codes"].append("mcp_unavailable")
        return EXIT_MCP_UNAVAILABLE, _finalize(payload, started_mono)

    resources = read_comfy_resources(host, port, args.timeout_seconds)
    payload["resource_probe"] = resources

    if not resources.get("ok"):
        payload["status"] = "resource_unavailable"
        payload["reason_codes"].append("mcp_unavailable")
        return EXIT_RESOURCE_UNAVAILABLE, _finalize(payload, started_mono)

    reads = resources.get("reads", {})
    comfy_status_payload = reads.get("shim.comfy.status", {}).get("payload")
    comfy_queue_payload = reads.get("shim.comfy.queue", {}).get("payload")
    comfy_history_payload = reads.get("shim.comfy.history", {}).get("payload")

    validation = validate_comfy_resources(
        status_payload=comfy_status_payload,
        queue_payload=comfy_queue_payload,
        history_payload=comfy_history_payload,
        status_max_age_seconds=settings["status_max_age_seconds"],
        max_hints=settings["max_hints"],
    )
    validation["cloud_fallback_count"] = 0
    payload["validation"] = validation
    payload["guidance_hints"] = validation.get("guidance_hints", [])

    if validation.get("status") != "ok":
        payload["status"] = "validation_failed"
        payload["reason_codes"].extend(validation.get("reason_codes", []))
        return EXIT_VALIDATION_FAILED, _finalize(payload, started_mono)

    payload["status"] = "ok"
    return EXIT_SUCCESS, _finalize(payload, started_mono)


def _write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    code, payload = run(args)
    repo_root = Path(args.repo_root).expanduser().resolve()
    out_path = Path(args.json_out).expanduser()
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    out_path = out_path.resolve()
    _write_output(out_path, payload)
    print(f"status={payload['status']} exit_code={code} json_out={out_path.as_posix()}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
