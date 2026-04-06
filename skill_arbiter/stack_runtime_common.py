from __future__ import annotations

from typing import Any


def _first_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return default


def _first_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        return max(minimum, int(value))
    except (TypeError, ValueError):
        return default


def _first_dict(row: dict[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _pick_str(row: dict[str, Any], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = _first_str(row.get(key), "")
        if value:
            return value
    return default


def _pick_dict(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        candidate = row.get(key)
        if isinstance(candidate, dict):
            return candidate
    return {}


def _sanitize_path_hint(value: str) -> str:
    raw = _first_str(value, "")
    if not raw:
        return ""
    normalized = raw.replace("\\", "/").rstrip("/")
    if "/" not in normalized:
        return normalized[:120]
    leaf = normalized.split("/")[-1]
    return leaf[:120]
