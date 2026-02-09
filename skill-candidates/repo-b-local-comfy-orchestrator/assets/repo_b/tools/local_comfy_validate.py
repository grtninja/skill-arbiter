#!/usr/bin/env python3
"""Validate Comfy MCP resource payloads for local orchestration."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATUS_MAX_AGE_SECONDS = 60
DEFAULT_MAX_HINTS = 12
MAX_HISTORY_ROWS = 500

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
REASON_ORDER = (
    "mcp_unavailable",
    "comfy_disabled",
    "comfy_unreachable",
    "schema_invalid",
    "stale_status",
    "policy_violation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Comfy MCP resources and emit guidance hints")
    parser.add_argument("--status-json", required=True, help="Path to shim.comfy.status JSON")
    parser.add_argument("--queue-json", required=True, help="Path to shim.comfy.queue JSON")
    parser.add_argument("--history-json", required=True, help="Path to shim.comfy.history JSON")
    parser.add_argument(
        "--status-max-age-seconds",
        type=int,
        default=DEFAULT_STATUS_MAX_AGE_SECONDS,
        help="Maximum allowed age for status checked_at",
    )
    parser.add_argument("--max-hints", type=int, default=DEFAULT_MAX_HINTS, help="Maximum emitted hints")
    parser.add_argument("--json-out", default="", help="Optional report output path")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now_epoch() -> float:
    return datetime.now(timezone.utc).timestamp()


def _parse_iso_epoch(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        candidate = text.replace("Z", "+00:00")
        return datetime.fromisoformat(candidate).timestamp()
    except ValueError:
        return None


def _dedupe_reasons(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in REASON_ORDER:
        if reason in values and reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    for reason in values:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return ordered


def _normalize_priority(value: str) -> str:
    candidate = str(value or "").strip().lower()
    if candidate in PRIORITY_ORDER:
        return candidate
    return "medium"


def _hint(resource: str, finding: str, evidence: list[str], confidence: float, priority: str) -> dict[str, Any]:
    score = max(0.0, min(float(confidence), 1.0))
    return {
        "resource": str(resource),
        "finding": str(finding),
        "evidence": [str(item) for item in evidence if str(item).strip()],
        "confidence": round(score, 4),
        "priority": _normalize_priority(priority),
    }


def _sort_hints(hints: list[dict[str, Any]], max_hints: int) -> list[dict[str, Any]]:
    hints.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(str(item.get("priority", "")), 99),
            -float(item.get("confidence", 0.0)),
            str(item.get("resource", "")),
            str(item.get("finding", "")),
        )
    )
    return hints[: max(max_hints, 1)]


def validate_comfy_resources(
    status_payload: Any,
    queue_payload: Any,
    history_payload: Any,
    *,
    status_max_age_seconds: int = DEFAULT_STATUS_MAX_AGE_SECONDS,
    max_hints: int = DEFAULT_MAX_HINTS,
    now_epoch: float | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    hints: list[dict[str, Any]] = []
    now_ts = _utc_now_epoch() if now_epoch is None else float(now_epoch)

    status_ok = True
    queue_ok = True
    history_ok = True
    status_age_seconds: float | None = None

    if not isinstance(status_payload, dict):
        status_ok = False
        reasons.append("schema_invalid")
        hints.append(
            _hint(
                "shim.comfy.status",
                "Status resource must be a JSON object.",
                [f"received_type={type(status_payload).__name__}"],
                0.99,
                "high",
            )
        )
    else:
        enabled = status_payload.get("enabled") is True
        reachable = status_payload.get("reachable") is True
        last_error = str(status_payload.get("last_error") or "").strip()
        checked_at = status_payload.get("checked_at")
        checked_epoch = _parse_iso_epoch(checked_at)

        if not enabled:
            status_ok = False
            reasons.append("comfy_disabled")
            hints.append(
                _hint(
                    "shim.comfy.status",
                    "ComfyUI integration is disabled.",
                    ["expected enabled=true"],
                    0.98,
                    "high",
                )
            )
        if not reachable or last_error:
            status_ok = False
            reasons.append("comfy_unreachable")
            evidence = ["expected reachable=true"]
            if last_error:
                evidence.append(f"last_error={last_error}")
            hints.append(
                _hint(
                    "shim.comfy.status",
                    "ComfyUI endpoint is not reachable.",
                    evidence,
                    0.97,
                    "high",
                )
            )
        if checked_epoch is None:
            status_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.status",
                    "checked_at timestamp is missing or invalid.",
                    [f"checked_at={checked_at!r}"],
                    0.95,
                    "high",
                )
            )
        else:
            status_age_seconds = max(0.0, now_ts - checked_epoch)
            if status_age_seconds > max(int(status_max_age_seconds), 1):
                status_ok = False
                reasons.append("stale_status")
                hints.append(
                    _hint(
                        "shim.comfy.status",
                        "Status probe is stale.",
                        [
                            f"status_age_seconds={round(status_age_seconds, 3)}",
                            f"max_age_seconds={max(int(status_max_age_seconds), 1)}",
                        ],
                        0.96,
                        "high",
                    )
                )

    if not isinstance(queue_payload, dict):
        queue_ok = False
        reasons.append("schema_invalid")
        hints.append(
            _hint(
                "shim.comfy.queue",
                "Queue resource must be a JSON object.",
                [f"received_type={type(queue_payload).__name__}"],
                0.94,
                "high",
            )
        )
    else:
        running_ids = queue_payload.get("running_prompt_ids")
        pending_ids = queue_payload.get("pending_prompt_ids")
        running_count = queue_payload.get("running_count")
        pending_count = queue_payload.get("pending_count")

        if not isinstance(running_ids, list) or not isinstance(pending_ids, list):
            queue_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.queue",
                    "Queue prompt ID lists are invalid.",
                    ["expected list running_prompt_ids + pending_prompt_ids"],
                    0.95,
                    "high",
                )
            )
        if not isinstance(running_count, int) or not isinstance(pending_count, int):
            queue_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.queue",
                    "Queue counts are invalid.",
                    ["expected integer running_count + pending_count"],
                    0.95,
                    "high",
                )
            )

        if isinstance(running_ids, list) and isinstance(running_count, int) and running_count != len(running_ids):
            queue_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.queue",
                    "running_count does not match running_prompt_ids length.",
                    [f"running_count={running_count}", f"len={len(running_ids)}"],
                    0.96,
                    "high",
                )
            )

        if isinstance(pending_ids, list) and isinstance(pending_count, int) and pending_count != len(pending_ids):
            queue_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.queue",
                    "pending_count does not match pending_prompt_ids length.",
                    [f"pending_count={pending_count}", f"len={len(pending_ids)}"],
                    0.96,
                    "high",
                )
            )

    if not isinstance(history_payload, dict):
        history_ok = False
        reasons.append("schema_invalid")
        hints.append(
            _hint(
                "shim.comfy.history",
                "History resource must be a JSON object.",
                [f"received_type={type(history_payload).__name__}"],
                0.94,
                "high",
            )
        )
    else:
        entries = history_payload.get("entries")
        count = history_payload.get("count")
        if not isinstance(entries, list) or not isinstance(count, int):
            history_ok = False
            reasons.append("schema_invalid")
            hints.append(
                _hint(
                    "shim.comfy.history",
                    "History entries/count fields are invalid.",
                    ["expected list entries + integer count"],
                    0.95,
                    "high",
                )
            )
        else:
            if count != len(entries):
                history_ok = False
                reasons.append("schema_invalid")
                hints.append(
                    _hint(
                        "shim.comfy.history",
                        "History count does not match entries length.",
                        [f"count={count}", f"len={len(entries)}"],
                        0.96,
                        "high",
                    )
                )
            if count > MAX_HISTORY_ROWS:
                history_ok = False
                reasons.append("schema_invalid")
                hints.append(
                    _hint(
                        "shim.comfy.history",
                        "History row count exceeds deterministic bound.",
                        [f"count={count}", f"max={MAX_HISTORY_ROWS}"],
                        0.92,
                        "medium",
                    )
                )

            for index, row in enumerate(entries):
                if not isinstance(row, dict):
                    history_ok = False
                    reasons.append("schema_invalid")
                    hints.append(
                        _hint(
                            "shim.comfy.history",
                            "History entry is not an object.",
                            [f"index={index}", f"type={type(row).__name__}"],
                            0.93,
                            "high",
                        )
                    )
                    break
                if not isinstance(row.get("prompt_id"), str) or not row.get("prompt_id", "").strip():
                    history_ok = False
                    reasons.append("schema_invalid")
                    hints.append(
                        _hint(
                            "shim.comfy.history",
                            "History entry prompt_id is missing or invalid.",
                            [f"index={index}"],
                            0.94,
                            "high",
                        )
                    )
                    break
                if not isinstance(row.get("queue_state"), str):
                    history_ok = False
                    reasons.append("schema_invalid")
                    hints.append(
                        _hint(
                            "shim.comfy.history",
                            "History entry queue_state must be a string.",
                            [f"index={index}"],
                            0.93,
                            "high",
                        )
                    )
                    break
                if not isinstance(row.get("has_outputs"), bool):
                    history_ok = False
                    reasons.append("schema_invalid")
                    hints.append(
                        _hint(
                            "shim.comfy.history",
                            "History entry has_outputs must be a bool.",
                            [f"index={index}"],
                            0.93,
                            "high",
                        )
                    )
                    break
                if not isinstance(row.get("node_count"), int):
                    history_ok = False
                    reasons.append("schema_invalid")
                    hints.append(
                        _hint(
                            "shim.comfy.history",
                            "History entry node_count must be an int.",
                            [f"index={index}"],
                            0.93,
                            "high",
                        )
                    )
                    break

    if status_ok and queue_ok and history_ok:
        hints.extend(
            [
                _hint(
                    "shim.comfy.status",
                    "Comfy status payload is healthy and fresh.",
                    [f"status_age_seconds={round(status_age_seconds or 0.0, 3)}"],
                    0.97,
                    "high",
                ),
                _hint(
                    "shim.comfy.queue",
                    "Queue payload is consistent.",
                    ["counts match running/pending list lengths"],
                    0.95,
                    "medium",
                ),
                _hint(
                    "shim.comfy.history",
                    "History payload shape is valid.",
                    ["entries/count contract verified"],
                    0.95,
                    "medium",
                ),
            ]
        )

    reason_codes = _dedupe_reasons(reasons)
    guidance_hints = _sort_hints(hints, max_hints=max_hints)
    status = "ok" if not reason_codes else "validation_failed"

    return {
        "status": status,
        "checks": {
            "status_ok": status_ok,
            "queue_ok": queue_ok,
            "history_ok": history_ok,
        },
        "status_age_seconds": round(status_age_seconds, 4) if status_age_seconds is not None else None,
        "reason_codes": reason_codes,
        "hint_count": len(guidance_hints),
        "guidance_hints": guidance_hints,
        "cloud_fallback_count": 0,
    }


def main() -> int:
    args = parse_args()
    status_payload = read_json(Path(args.status_json).expanduser().resolve())
    queue_payload = read_json(Path(args.queue_json).expanduser().resolve())
    history_payload = read_json(Path(args.history_json).expanduser().resolve())

    report = validate_comfy_resources(
        status_payload=status_payload,
        queue_payload=queue_payload,
        history_payload=history_payload,
        status_max_age_seconds=max(int(args.status_max_age_seconds), 1),
        max_hints=max(int(args.max_hints), 1),
    )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
