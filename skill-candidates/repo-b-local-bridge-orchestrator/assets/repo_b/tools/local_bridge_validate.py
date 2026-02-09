#!/usr/bin/env python3
"""Validate read-only bridge responses for local guidance hints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

DEFAULT_CONFIDENCE_MIN = 0.85
DEFAULT_EVIDENCE_MIN = 2
DEFAULT_COVERAGE_MIN = 0.70
DEFAULT_MAX_HINTS = 12

REASON_PRIORITY = (
    "schema_invalid",
    "unauthorized_path",
    "low_confidence",
    "insufficient_evidence",
)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate bridge responses and emit normalized guidance hints"
    )
    parser.add_argument("--response-json", required=True, help="Bridge response JSON file path")
    parser.add_argument(
        "--candidate-paths-json",
        default="",
        help="Optional candidate paths JSON file (list[str] or index_query payload)",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument(
        "--allowed-root",
        action="append",
        default=[],
        help="Allowed root path (repeatable). Default is --repo-root.",
    )
    parser.add_argument("--confidence-min", type=float, default=DEFAULT_CONFIDENCE_MIN)
    parser.add_argument("--evidence-min", type=int, default=DEFAULT_EVIDENCE_MIN)
    parser.add_argument("--coverage-min", type=float, default=DEFAULT_COVERAGE_MIN)
    parser.add_argument("--max-hints", type=int, default=DEFAULT_MAX_HINTS)
    parser.add_argument("--json-out", default="", help="Optional output JSON file")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonicalize_rel_path(path_text: str, repo_root: Path) -> str:
    clean = path_text.strip().replace("\\", "/")
    if not clean:
        return ""
    candidate = Path(clean)
    resolved = candidate if candidate.is_absolute() else (repo_root / candidate)
    try:
        rel = resolved.resolve().relative_to(repo_root.resolve())
        return rel.as_posix()
    except ValueError:
        return resolved.resolve().as_posix()


def parse_candidate_paths(payload: Any, repo_root: Path) -> list[str]:
    values: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                rel = _canonicalize_rel_path(item, repo_root)
                if rel:
                    values.append(rel)
    elif isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    rel = _canonicalize_rel_path(item["path"], repo_root)
                    if rel:
                        values.append(rel)
    deduped: list[str] = []
    seen: set[str] = set()
    for path in values:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def normalize_evidence(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
    return items


def clamp_confidence(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    if parsed < 0.0:
        return 0.0
    if parsed > 1.0:
        return 1.0
    return parsed


def normalize_priority(value: Any, confidence: float) -> str:
    if isinstance(value, str):
        text = value.strip().lower()
        if text in PRIORITY_ORDER:
            return text
    if confidence >= 0.92:
        return "high"
    if confidence >= DEFAULT_CONFIDENCE_MIN:
        return "medium"
    return "low"


def is_within(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def extract_hint_lists(payload: Any) -> list[list[dict[str, Any]]]:
    if payload is None:
        return []
    lists: list[list[dict[str, Any]]] = []
    seen_ids: set[int] = set()
    stack: list[Any] = [payload]
    preferred_keys = {"guidance_hints", "hints", "findings", "citations"}

    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if (
                    key in preferred_keys
                    and isinstance(value, list)
                    and value
                    and all(isinstance(item, dict) for item in value)
                    and id(value) not in seen_ids
                ):
                    seen_ids.add(id(value))
                    lists.append(value)
                if isinstance(value, (dict, list)):
                    stack.append(value)
            continue

        if isinstance(node, list):
            if (
                node
                and all(isinstance(item, dict) for item in node)
                and any(
                    any(field in item for field in ("path", "finding", "evidence", "confidence"))
                    for item in node
                )
                and id(node) not in seen_ids
            ):
                seen_ids.add(id(node))
                lists.append(node)
            for item in node:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    return lists


def dedupe_reasons(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for key in REASON_PRIORITY:
        if key in values and key not in seen:
            seen.add(key)
            deduped.append(key)
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def validate_bridge_response(
    payload: Any,
    candidate_paths: list[str],
    repo_root: Path,
    allowed_roots: list[Path],
    confidence_min: float = DEFAULT_CONFIDENCE_MIN,
    evidence_min: int = DEFAULT_EVIDENCE_MIN,
    coverage_min: float = DEFAULT_COVERAGE_MIN,
    max_hints: int = DEFAULT_MAX_HINTS,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    normalized_candidates = parse_candidate_paths(candidate_paths, repo_root)
    candidate_set = set(normalized_candidates)

    reasons: list[str] = []
    unauthorized_paths: list[str] = []
    normalized_hints: list[dict[str, Any]] = []

    for hint_list in extract_hint_lists(payload):
        for item in hint_list:
            path_raw = item.get("path")
            finding_raw = item.get("finding", item.get("summary", item.get("claim", "")))
            if not isinstance(path_raw, str):
                continue
            finding = str(finding_raw).strip()
            if not finding:
                continue

            clean_path = path_raw.strip().replace("\\", "/")
            if not clean_path:
                continue
            path_value = Path(clean_path)
            resolved_path = (
                path_value.resolve() if path_value.is_absolute() else (repo_root / path_value).resolve()
            )
            if not is_within(resolved_path, allowed_roots):
                unauthorized_paths.append(clean_path)
                continue

            rel_path = _canonicalize_rel_path(clean_path, repo_root)
            confidence = clamp_confidence(
                item.get("confidence", item.get("score", item.get("confidence_score", 0.0)))
            )
            evidence = normalize_evidence(
                item.get("evidence", item.get("citations", item.get("supporting_evidence", [])))
            )
            priority = normalize_priority(item.get("priority", ""), confidence)

            normalized_hints.append(
                {
                    "path": rel_path,
                    "finding": finding,
                    "evidence": evidence,
                    "confidence": round(confidence, 4),
                    "priority": priority,
                }
            )

    if unauthorized_paths:
        reasons.append("unauthorized_path")

    if not normalized_hints:
        reasons.append("schema_invalid")

    evidence_hints = [item for item in normalized_hints if item["evidence"]]
    evidence_count = len(evidence_hints)
    if evidence_count < max(evidence_min, 1):
        reasons.append("insufficient_evidence")

    if candidate_set:
        cited = {item["path"] for item in evidence_hints if item["path"] in candidate_set}
        coverage_ratio = len(cited) / len(candidate_set)
    else:
        coverage_ratio = 0.0
    if coverage_ratio < max(min(coverage_min, 1.0), 0.0):
        reasons.append("insufficient_evidence")

    confidence_pool = evidence_hints if evidence_hints else normalized_hints
    if confidence_pool:
        confidence_score = sum(item["confidence"] for item in confidence_pool) / len(confidence_pool)
    else:
        confidence_score = 0.0
    if confidence_score < max(min(confidence_min, 1.0), 0.0):
        reasons.append("low_confidence")

    normalized_hints.sort(
        key=lambda item: (
            PRIORITY_ORDER.get(item["priority"], 99),
            -item["confidence"],
            item["path"],
            item["finding"],
        )
    )
    trimmed_hints = normalized_hints[: max(max_hints, 1)]

    status = "ok" if not reasons else "validation_failed"
    return {
        "status": status,
        "confidence_score": round(confidence_score, 4),
        "evidence_count": evidence_count,
        "coverage_ratio": round(coverage_ratio, 4),
        "candidate_count": len(candidate_set),
        "hint_count": len(trimmed_hints),
        "reason_codes": dedupe_reasons(reasons),
        "unauthorized_paths": sorted(set(unauthorized_paths)),
        "guidance_hints": trimmed_hints,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    response_path = Path(args.response_json).expanduser().resolve()
    if not response_path.is_file():
        raise SystemExit(f"error: response JSON file not found: {response_path}")

    payload = read_json(response_path)
    candidate_paths: list[str] = []
    if args.candidate_paths_json:
        candidate_payload = read_json(Path(args.candidate_paths_json).expanduser().resolve())
        candidate_paths = parse_candidate_paths(candidate_payload, repo_root)

    allowed_roots = [Path(value).expanduser().resolve() for value in args.allowed_root]
    if not allowed_roots:
        allowed_roots = [repo_root]

    report = validate_bridge_response(
        payload=payload,
        candidate_paths=candidate_paths,
        repo_root=repo_root,
        allowed_roots=allowed_roots,
        confidence_min=args.confidence_min,
        evidence_min=args.evidence_min,
        coverage_min=args.coverage_min,
        max_hints=args.max_hints,
    )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
