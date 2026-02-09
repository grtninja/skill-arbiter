#!/usr/bin/env python3
"""Manual local bridge orchestrator with strict fail-closed validation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from local_bridge_validate import validate_bridge_response
except ImportError as exc:
    validate_bridge_response = None
    VALIDATOR_IMPORT_ERROR = str(exc)
else:
    VALIDATOR_IMPORT_ERROR = ""

EXIT_SUCCESS = 0
EXIT_BRIDGE_UNAVAILABLE = 10
EXIT_INDEX_UNAVAILABLE = 11
EXIT_VALIDATION_FAILED = 12
EXIT_POLICY_VIOLATION = 13

DEFAULT_BRIDGE_URL = "http://127.0.0.1:9000"
DEFAULT_SCOPE = ("connector", "service", "route", "config")
DEFAULT_LIMIT = 200
DEFAULT_TIMEOUT_SECONDS = 8.0
DEFAULT_COVERAGE_MIN = 0.70
DEFAULT_CONFIDENCE_MIN = 0.85
DEFAULT_EVIDENCE_MIN = 2
DEFAULT_MAX_HINTS = 12

INDEX_STOP_REASONS = {
    "max_files_per_run_reached",
    "max_seconds_reached",
    "max_read_bytes_reached",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local bridge orchestration in fail-closed mode")
    parser.add_argument("--task", required=True, help="Task identifier")
    parser.add_argument("--prompt-file", required=True, help="Prompt text file path")
    parser.add_argument("--scope", required=True, choices=DEFAULT_SCOPE, help="Index query scope")
    parser.add_argument("--json-out", required=True, help="Output JSON report path")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--index-dir", default=".codex-index", help="Index directory")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL, help="Bridge API base URL")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Max candidate paths per orchestration run",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout for bridge requests",
    )
    return parser.parse_args()


def env_is_enabled(value: str | None, default: bool = True) -> bool:
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def parse_env_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def parse_env_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def parse_allowed_roots(raw_value: str, repo_root: Path) -> list[Path]:
    raw_value = raw_value.strip()
    if not raw_value:
        return [repo_root.resolve()]
    parts = [part.strip() for part in raw_value.split(",") if part.strip()]
    roots: list[Path] = []
    for part in parts:
        clean = part.replace("\\", "/")
        root = Path(clean).expanduser()
        if not root.is_absolute():
            root = repo_root / root
        roots.append(root.resolve())
    return roots if roots else [repo_root.resolve()]


def scope_query_specs(scope: str) -> list[dict[str, str]]:
    if scope == "connector":
        return [{"path_contains": "connector"}]
    if scope == "service":
        return [{"path_contains": "service"}]
    if scope == "route":
        return [{"path_contains": "route", "ext": "py"}]
    if scope == "config":
        return [
            {"ext": "yaml"},
            {"ext": "yml"},
            {"ext": "json"},
            {"ext": "toml"},
        ]
    raise ValueError(f"unsupported scope: {scope}")


def should_retry_index(candidate_paths: list[str], run_report: dict[str, Any]) -> bool:
    if candidate_paths:
        return False
    status = str(run_report.get("status", "")).lower()
    stop_reason = str(run_report.get("stop_reason", "")).lower()
    return status == "partial" and stop_reason in INDEX_STOP_REASONS


def request_json(
    method: str,
    url: str,
    timeout_seconds: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    body: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    request = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
            parsed = json.loads(raw) if raw else {}
            return {
                "ok": True,
                "status": int(getattr(response, "status", 200)),
                "payload": parsed,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        message = f"http_error:{exc.code}"
        try:
            body_text = exc.read().decode("utf-8", errors="replace").strip()
        except OSError:
            body_text = ""
        if body_text:
            message = f"{message}:{body_text[:180]}"
        return {"ok": False, "status": int(exc.code), "payload": {}, "error": message}
    except urllib.error.URLError as exc:
        return {"ok": False, "status": 0, "payload": {}, "error": f"url_error:{exc.reason}"}
    except TimeoutError:
        return {"ok": False, "status": 0, "payload": {}, "error": "timeout"}


def summarize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {"type": "object", "keys": sorted(payload.keys())[:25]}
    if isinstance(payload, list):
        return {"type": "array", "count": len(payload)}
    return {"type": type(payload).__name__}


def probe_bridge(base_url: str, timeout_seconds: float) -> dict[str, Any]:
    base = base_url.rstrip("/")
    health = request_json("GET", f"{base}/health", timeout_seconds)
    capabilities = request_json("GET", f"{base}/api/agent/capabilities", timeout_seconds)
    ok = bool(health["ok"] and capabilities["ok"])
    return {
        "ok": ok,
        "health": {
            "ok": health["ok"],
            "status": health["status"],
            "error": health["error"],
            "summary": summarize_payload(health["payload"]),
        },
        "capabilities": {
            "ok": capabilities["ok"],
            "status": capabilities["status"],
            "error": capabilities["error"],
            "summary": summarize_payload(capabilities["payload"]),
        },
    }


def find_safe_index_scripts(repo_root: Path) -> tuple[Path, Path]:
    roots: list[Path] = []
    override = os.environ.get("REPO_B_SAFE_INDEX_SCRIPTS", "").strip()
    if override:
        roots.append(Path(override).expanduser())

    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        roots.append(Path(codex_home).expanduser() / "skills" / "safe-mass-index-core" / "scripts")

    roots.append(Path.home() / ".codex" / "skills" / "safe-mass-index-core" / "scripts")
    roots.append(repo_root / ".codex" / "skills" / "safe-mass-index-core" / "scripts")

    for root in roots:
        build_script = root / "index_build.py"
        query_script = root / "index_query.py"
        if build_script.is_file() and query_script.is_file():
            return build_script.resolve(), query_script.resolve()
    raise FileNotFoundError("safe-mass-index-core scripts not found")


def run_subprocess(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def run_index_build(
    build_script: Path,
    repo_root: Path,
    index_dir: Path,
    max_seconds: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(build_script),
        "--repo-root",
        ".",
        "--index-dir",
        str(index_dir),
        "--mode",
        "incremental",
        "--max-files-per-run",
        "12000",
        "--max-seconds",
        str(max_seconds),
        "--max-read-bytes",
        "67108864",
        "--exclude-dir",
        ".git",
        "--exclude-dir",
        "node_modules",
        "--exclude-dir",
        ".venv",
        "--exclude-dir",
        "venv",
        "--exclude-dir",
        "__pycache__",
        "--exclude-dir",
        "build",
        "--exclude-dir",
        "dist",
        "--exclude-dir",
        "target",
        "--exclude-dir",
        ".cache",
        "--exclude-dir",
        ".codex-index",
        "--json-out",
        str(index_dir / "run.json"),
    ]
    result = run_subprocess(command, cwd=repo_root)
    run_report = load_json(repo_root / index_dir / "run.json")
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "command": command,
        "stdout_tail": "\n".join(result.stdout.strip().splitlines()[-5:]),
        "stderr_tail": "\n".join(result.stderr.strip().splitlines()[-5:]),
        "report": run_report,
    }


def run_index_query(
    query_script: Path,
    repo_root: Path,
    index_dir: Path,
    limit: int,
    spec: dict[str, str],
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(query_script),
        "--index-dir",
        str(index_dir),
        "--limit",
        str(limit),
        "--format",
        "json",
    ]
    if spec.get("path_contains"):
        command.extend(["--path-contains", spec["path_contains"]])
    if spec.get("ext"):
        command.extend(["--ext", spec["ext"]])

    result = run_subprocess(command, cwd=repo_root)
    if result.returncode != 0:
        return {
            "ok": False,
            "returncode": result.returncode,
            "spec": spec,
            "command": command,
            "rows": [],
            "stderr_tail": "\n".join(result.stderr.strip().splitlines()[-5:]),
        }

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "returncode": result.returncode,
            "spec": spec,
            "command": command,
            "rows": [],
            "stderr_tail": "invalid_json_output",
        }

    rows = parsed.get("results", []) if isinstance(parsed, dict) else []
    valid_rows = [row for row in rows if isinstance(row, dict) and isinstance(row.get("path"), str)]
    return {
        "ok": True,
        "returncode": result.returncode,
        "spec": spec,
        "command": command,
        "rows": valid_rows,
        "stderr_tail": "",
    }


def collect_candidate_paths(query_runs: list[dict[str, Any]], limit: int) -> list[str]:
    values: list[str] = []
    for run in query_runs:
        for row in run.get("rows", []):
            path = row.get("path")
            if isinstance(path, str):
                values.append(path.replace("\\", "/").strip())
    return dedupe([item for item in values if item])[: max(limit, 1)]


def load_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("prompt file is empty")
    return text


def build_task_payload(task_id: str, scope: str, prompt: str, paths: list[str]) -> dict[str, Any]:
    return {
        "task_type": "analyze_files",
        "prompt": prompt,
        "paths": paths,
        "allow_write": False,
        "dry_run": True,
        "metadata": {
            "task_id": task_id,
            "scope": scope,
            "source": "repo-b-local-bridge-orchestrator",
        },
    }


def policy_settings(environ: dict[str, str]) -> dict[str, Any]:
    reasons: list[str] = []
    if not env_is_enabled(environ.get("REPO_B_LOCAL_ORCH_ENABLED"), default=True):
        reasons.append("policy_violation")

    fail_closed = env_is_enabled(environ.get("REPO_B_LOCAL_ORCH_FAIL_CLOSED"), default=True)
    if not fail_closed:
        reasons.append("policy_violation")

    continue_mode = environ.get("REPO_B_CONTINUE_MODE", "read_only").strip().lower()
    if continue_mode != "read_only":
        reasons.append("policy_violation")

    bridge_enabled = environ.get("REPO_B_CONTINUE_BRIDGE_ENABLED", "1")
    if not env_is_enabled(bridge_enabled, default=True):
        reasons.append("policy_violation")

    confidence_min = parse_env_float(
        environ.get("REPO_B_LOCAL_ORCH_CONFIDENCE_MIN"), DEFAULT_CONFIDENCE_MIN
    )
    evidence_min = parse_env_int(environ.get("REPO_B_LOCAL_ORCH_EVIDENCE_MIN"), DEFAULT_EVIDENCE_MIN)
    max_hints = parse_env_int(environ.get("REPO_B_LOCAL_ORCH_MAX_HINTS"), DEFAULT_MAX_HINTS)

    return {
        "ok": not reasons,
        "reason_codes": dedupe(reasons),
        "fail_closed": fail_closed,
        "confidence_min": max(min(confidence_min, 1.0), 0.0),
        "evidence_min": max(evidence_min, 1),
        "max_hints": max(max_hints, 1),
    }


def output_template(task_id: str) -> dict[str, Any]:
    return {
        "status": "unknown",
        "task_id": task_id,
        "bridge_probe": {"ok": False},
        "index_run": {"status": "not_run"},
        "validation": {"status": "not_run", "reason_codes": [], "cloud_fallback_count": 0},
        "guidance_hints": [],
        "timing_ms": 0,
        "reason_codes": [],
    }


def finalize_payload(payload: dict[str, Any], started_mono: float) -> dict[str, Any]:
    payload["reason_codes"] = dedupe([str(item) for item in payload.get("reason_codes", []) if str(item)])
    payload["timing_ms"] = int((time.monotonic() - started_mono) * 1000)
    return payload


def run(args: argparse.Namespace, environ: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    started_mono = time.monotonic()
    env = dict(os.environ if environ is None else environ)
    repo_root = Path(args.repo_root).expanduser().resolve()
    prompt_path = Path(args.prompt_file).expanduser().resolve()
    index_dir = Path(args.index_dir)
    output = output_template(args.task)

    settings = policy_settings(env)
    if not settings["ok"]:
        output["status"] = "policy_violation"
        output["reason_codes"].extend(settings["reason_codes"])
        return EXIT_POLICY_VIOLATION, finalize_payload(output, started_mono)

    if validate_bridge_response is None:
        output["status"] = "policy_violation"
        output["reason_codes"].append("policy_violation")
        output["validation"] = {
            "status": "validator_unavailable",
            "reason_codes": ["schema_invalid"],
            "detail": VALIDATOR_IMPORT_ERROR,
            "cloud_fallback_count": 0,
        }
        return EXIT_POLICY_VIOLATION, finalize_payload(output, started_mono)

    if not prompt_path.is_file():
        output["status"] = "policy_violation"
        output["reason_codes"].append("policy_violation")
        output["validation"] = {
            "status": "prompt_not_found",
            "reason_codes": ["schema_invalid"],
            "cloud_fallback_count": 0,
        }
        return EXIT_POLICY_VIOLATION, finalize_payload(output, started_mono)

    probe = probe_bridge(args.bridge_url, args.timeout_seconds)
    output["bridge_probe"] = probe
    if not probe["ok"]:
        output["status"] = "bridge_unavailable"
        output["reason_codes"].append("bridge_unreachable")
        return EXIT_BRIDGE_UNAVAILABLE, finalize_payload(output, started_mono)

    try:
        build_script, query_script = find_safe_index_scripts(repo_root)
    except FileNotFoundError:
        output["status"] = "index_unavailable"
        output["reason_codes"].append("index_unavailable")
        output["index_run"] = {"status": "scripts_not_found"}
        return EXIT_INDEX_UNAVAILABLE, finalize_payload(output, started_mono)

    build_runs: list[dict[str, Any]] = []
    query_runs: list[dict[str, Any]] = []
    all_candidates: list[str] = []
    retry_performed = False

    first_build = run_index_build(build_script, repo_root, index_dir, max_seconds=25)
    build_runs.append(first_build)
    if not first_build["ok"]:
        output["status"] = "index_unavailable"
        output["reason_codes"].append("index_unavailable")
        output["index_run"] = {
            "status": "build_failed",
            "retry_performed": False,
            "build_runs": build_runs,
            "query_runs": query_runs,
            "candidate_count": 0,
        }
        return EXIT_INDEX_UNAVAILABLE, finalize_payload(output, started_mono)

    for spec in scope_query_specs(args.scope):
        query_run = run_index_query(query_script, repo_root, index_dir, args.limit, spec)
        query_runs.append(query_run)
    all_candidates = collect_candidate_paths(query_runs, args.limit)

    run_report = first_build.get("report", {})
    if should_retry_index(all_candidates, run_report):
        retry_performed = True
        second_build = run_index_build(build_script, repo_root, index_dir, max_seconds=40)
        build_runs.append(second_build)
        if second_build["ok"]:
            query_runs = []
            for spec in scope_query_specs(args.scope):
                query_run = run_index_query(query_script, repo_root, index_dir, args.limit, spec)
                query_runs.append(query_run)
            all_candidates = collect_candidate_paths(query_runs, args.limit)

    output["index_run"] = {
        "status": "ok" if all_candidates else "no_candidates",
        "retry_performed": retry_performed,
        "build_runs": build_runs,
        "query_runs": query_runs,
        "candidate_count": len(all_candidates),
        "sample_paths": all_candidates[:20],
    }

    if not all_candidates:
        output["status"] = "index_unavailable"
        output["reason_codes"].append("index_unavailable")
        return EXIT_INDEX_UNAVAILABLE, finalize_payload(output, started_mono)

    try:
        prompt_text = load_prompt(prompt_path)
    except (OSError, ValueError):
        output["status"] = "policy_violation"
        output["reason_codes"].append("policy_violation")
        output["validation"] = {
            "status": "prompt_invalid",
            "reason_codes": ["schema_invalid"],
            "cloud_fallback_count": 0,
        }
        return EXIT_POLICY_VIOLATION, finalize_payload(output, started_mono)

    task_body = build_task_payload(args.task, args.scope, prompt_text, all_candidates)
    bridge_task = request_json(
        "POST",
        f"{args.bridge_url.rstrip('/')}/api/agent/tasks",
        args.timeout_seconds,
        payload=task_body,
    )
    if not bridge_task["ok"]:
        output["status"] = "bridge_unavailable"
        output["reason_codes"].append("bridge_unreachable")
        return EXIT_BRIDGE_UNAVAILABLE, finalize_payload(output, started_mono)

    allowed_roots = parse_allowed_roots(env.get("REPO_B_CONTINUE_ALLOWED_ROOTS", ""), repo_root)
    validation = validate_bridge_response(
        payload=bridge_task["payload"],
        candidate_paths=all_candidates,
        repo_root=repo_root,
        allowed_roots=allowed_roots,
        confidence_min=settings["confidence_min"],
        evidence_min=settings["evidence_min"],
        coverage_min=DEFAULT_COVERAGE_MIN,
        max_hints=settings["max_hints"],
    )
    validation["cloud_fallback_count"] = 0
    output["validation"] = validation
    output["guidance_hints"] = validation.get("guidance_hints", [])

    if validation.get("status") != "ok":
        output["status"] = "validation_failed"
        output["reason_codes"].extend(validation.get("reason_codes", []))
        return EXIT_VALIDATION_FAILED, finalize_payload(output, started_mono)

    output["status"] = "ok"
    return EXIT_SUCCESS, finalize_payload(output, started_mono)


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    code, payload = run(args)
    out_path = Path(args.json_out).expanduser().resolve()
    write_output(out_path, payload)
    print(f"status={payload['status']} exit_code={code} json_out={out_path.as_posix()}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
