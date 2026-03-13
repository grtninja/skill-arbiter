from __future__ import annotations

import json
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 5.0


def _optional_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _optional_int(value: Any) -> Optional[int]:
    result = _optional_float(value)
    if result is None:
        return None
    return int(result)


def _normalize_url(url: str) -> str:
    return str(url or "").strip().rstrip("/")


def _default_summary_url(health_url: str) -> str:
    parsed = urlparse(health_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid health url: {health_url!r}")
    return f"{parsed.scheme}://{parsed.netloc}/api/accounting/summary"


def fetch_json(url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    req = Request(_normalize_url(url), method="GET")
    with urlopen(req, timeout=timeout_seconds) as response:  # nosec B310
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


def normalize_stack_accounting(
    health_payload: dict[str, Any],
    summary_payload: dict[str, Any] | None = None,
    *,
    health_url: str = "",
    summary_url: str = "",
) -> dict[str, Any]:
    telemetry = health_payload.get("telemetry") if isinstance(health_payload.get("telemetry"), dict) else {}
    accounting = telemetry.get("accounting") if isinstance(telemetry.get("accounting"), dict) else {}
    provenance = telemetry.get("provenance") if isinstance(telemetry.get("provenance"), dict) else {}
    runtime_step = telemetry.get("runtime_step") if isinstance(telemetry.get("runtime_step"), dict) else {}
    serving_request = telemetry.get("serving_request") if isinstance(telemetry.get("serving_request"), dict) else {}
    lmstudio_routing = telemetry.get("lmstudio_routing") if isinstance(telemetry.get("lmstudio_routing"), dict) else {}
    providers = telemetry.get("providers") if isinstance(telemetry.get("providers"), dict) else {}
    summary = summary_payload.get("summary") if isinstance((summary_payload or {}).get("summary"), dict) else {}
    groups = summary.get("groups") if isinstance(summary.get("groups"), list) else []

    authoritative_cost_state = str(
        telemetry.get("authoritative_cost_state")
        or accounting.get("authoritative_cost_state")
        or provenance.get("cost_state")
        or "suppressed"
    ).strip().lower()
    preview_cost_state = str(
        telemetry.get("preview_cost_state")
        or accounting.get("preview_cost_state")
        or "suppressed"
    ).strip().lower()

    displacement_value_preview = _optional_float(
        telemetry.get("displacement_value_preview")
        if "displacement_value_preview" in telemetry
        else accounting.get("displacement_value_preview")
    )
    displacement_value_preview_per_token = _optional_float(
        telemetry.get("displacement_value_preview_per_token")
        if "displacement_value_preview_per_token" in telemetry
        else accounting.get("displacement_value_preview_per_token")
    )
    benchmark_api_equivalent_cost = _optional_float(
        telemetry.get("benchmark_api_equivalent_cost")
        if "benchmark_api_equivalent_cost" in telemetry
        else accounting.get("benchmark_api_equivalent_cost")
    )

    summary_displacement_total = 0.0
    summary_benchmark_total = 0.0
    for row in groups:
        if not isinstance(row, dict):
            continue
        summary_displacement_total += float(
            _optional_float(row.get("displacement_value_preview")) or 0.0
        )
        summary_benchmark_total += float(
            _optional_float(row.get("benchmark_api_equivalent_cost")) or 0.0
        )

    if displacement_value_preview is None and summary_displacement_total > 0.0:
        displacement_value_preview = summary_displacement_total
    if benchmark_api_equivalent_cost is None and summary_benchmark_total > 0.0:
        benchmark_api_equivalent_cost = summary_benchmark_total
    if displacement_value_preview is None and benchmark_api_equivalent_cost is not None:
        displacement_value_preview = benchmark_api_equivalent_cost
    if preview_cost_state == "suppressed" and displacement_value_preview is not None:
        preview_cost_state = "priced"

    provider_names = sorted(key for key in providers.keys() if str(key).strip())
    lane_status_counts = {
        str(key): int(_optional_int(value) or 0)
        for key, value in (telemetry.get("lane_status_counts") or {}).items()
        if str(key).strip()
    }

    experimental_routes = int(lane_status_counts.get("experimental", 0))
    production_routes = int(lane_status_counts.get("production_real", 0))
    total_requests = int(_optional_int(telemetry.get("request_records_count")) or 0)
    metered_tpk_requests = int(_optional_int(telemetry.get("tpk_metered_requests")) or 0)

    local_ready = bool(health_payload.get("status") == "ok")
    routing_active = bool(lmstudio_routing.get("traffic_active"))
    preview_positive = bool((displacement_value_preview or 0.0) > 0.0)

    local_marginal_cost = _optional_float(accounting.get("local_marginal_cost"))
    if local_marginal_cost is None:
        local_marginal_cost = _optional_float(telemetry.get("verified_local_marginal_cost"))

    cloud_equivalent_cost = _optional_float(accounting.get("cloud_equivalent_cost"))
    if cloud_equivalent_cost is None:
        cloud_equivalent_cost = _optional_float(telemetry.get("cloud_equivalent_cost"))

    savings_vs_cloud_marginal = _optional_float(accounting.get("savings_vs_cloud_marginal"))
    if savings_vs_cloud_marginal is None:
        savings_vs_cloud_marginal = _optional_float(telemetry.get("savings_vs_cloud_marginal"))

    tpk_authoritative = _optional_float(
        telemetry.get("tpk_authoritative")
        if "tpk_authoritative" in telemetry
        else accounting.get("tpk_authoritative")
    )
    tpk_preview = _optional_float(
        telemetry.get("tpk_preview")
        if "tpk_preview" in telemetry
        else accounting.get("tpk_preview")
    )
    effective_tpk = _optional_float(telemetry.get("tpk"))
    tpk_source = "telemetry"
    if effective_tpk is None and tpk_authoritative is not None:
        effective_tpk = tpk_authoritative
        tpk_source = "authoritative"
    elif effective_tpk is None and tpk_preview is not None:
        effective_tpk = tpk_preview
        tpk_source = "preview"

    local_execution_hint = production_routes > 0 or routing_active or preview_positive or metered_tpk_requests > 0

    return {
        "available": True,
        "health_url": health_url,
        "summary_url": summary_url,
        "status": str(health_payload.get("status") or "").strip().lower(),
        "price_book_version": str(
            accounting.get("price_book_version")
            or ((summary_payload or {}).get("rate_card") or {}).get("version")
            or ""
        ).strip(),
        "tpk": effective_tpk,
        "tpk_source": tpk_source if effective_tpk is not None else "",
        "tpk_authoritative": tpk_authoritative,
        "tpk_preview": tpk_preview,
        "tpk_metered_requests": metered_tpk_requests,
        "tpk_metered_tokens": int(_optional_int(telemetry.get("tpk_metered_tokens")) or 0),
        "tpk_metered_energy_kwh": _optional_float(telemetry.get("tpk_metered_energy_kwh")),
        "authoritative_cost_state": authoritative_cost_state,
        "preview_cost_state": preview_cost_state,
        "displacement_value_preview": displacement_value_preview,
        "displacement_value_preview_per_token": displacement_value_preview_per_token,
        "benchmark_api_equivalent_cost": benchmark_api_equivalent_cost,
        "local_marginal_cost": local_marginal_cost,
        "cloud_equivalent_cost": cloud_equivalent_cost,
        "savings_vs_cloud_marginal": savings_vs_cloud_marginal,
        "measurement_state": str(
            telemetry.get("preview_energy_state")
            or accounting.get("preview_energy_state")
            or provenance.get("measurement_state")
            or ""
        ).strip().lower(),
        "preview_token_count_state": str(
            telemetry.get("preview_token_count_state")
            or accounting.get("preview_token_count_state")
            or provenance.get("token_count_state")
            or ""
        ).strip().lower(),
        "preview_energy_state": str(
            telemetry.get("preview_energy_state")
            or accounting.get("preview_energy_state")
            or provenance.get("measurement_state")
            or ""
        ).strip().lower(),
        "preview_mode": str(
            telemetry.get("preview_mode")
            or accounting.get("preview_mode")
            or ""
        ).strip().lower(),
        "runtime_latency_ms": _optional_float(runtime_step.get("latency_ms"))
        or _optional_float(telemetry.get("avg_latency_ms")),
        "serving_total_response_ms": _optional_float(serving_request.get("total_response_ms")),
        "provider_names": provider_names,
        "lane_status_counts": lane_status_counts,
        "routing_mode": str(lmstudio_routing.get("mode") or "").strip().lower(),
        "routing_active": routing_active,
        "local_ready": local_ready,
        "local_execution_hint": local_execution_hint,
        "preview_positive": preview_positive,
        "experimental_route_count": experimental_routes,
        "production_route_count": production_routes,
        "request_records_count": total_requests,
        "summary_group_count": int(_optional_int(summary.get("group_count")) or len(groups)),
    }


def fetch_stack_accounting(
    *,
    health_url: str,
    summary_url: str = "",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    normalized_health_url = _normalize_url(health_url)
    normalized_summary_url = _normalize_url(summary_url) if summary_url else _default_summary_url(normalized_health_url)
    health_payload = fetch_json(normalized_health_url, timeout_seconds=timeout_seconds)
    summary_payload = fetch_json(normalized_summary_url, timeout_seconds=timeout_seconds)
    return normalize_stack_accounting(
        health_payload,
        summary_payload,
        health_url=normalized_health_url,
        summary_url=normalized_summary_url,
    )
