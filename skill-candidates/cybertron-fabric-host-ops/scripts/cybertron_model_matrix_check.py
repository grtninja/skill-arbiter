#!/usr/bin/env python3
"""Validate the canonical Cybertron model matrix."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


CANONICAL_MATRIX = {
    "primary_general": "huihui-qwen3.5-4b-abliterated",
    "instruct_overflow": "huihui-qwen3-4b-instruct-2507-abliterated",
    "general_vision": "huihui-qwen3-vl-4b-instruct-abliterated",
    "coder": "qwen2.5-coder-1.5b-instruct-abliterated",
    "embeddings": "text-embedding-nomic-embed-text-v1.5",
}
ALIASES = {
    "text-embedding-nomic-embed-text-v1.5-embedding": "text-embedding-nomic-embed-text-v1.5",
}


@dataclass
class ModelMatrixReport:
    canonical: dict[str, str]
    observed: list[str]
    missing: list[str]
    extra: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the canonical Cybertron model matrix")
    parser.add_argument(
        "--observed-model",
        action="append",
        default=[],
        help="Observed model identifier (repeatable)",
    )
    parser.add_argument(
        "--observed-json",
        default="",
        help="Optional JSON file containing an observed model list or object with model names",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    return parser.parse_args()


def _normalize_model_id(value: str) -> str:
    model_id = value.strip()
    return ALIASES.get(model_id, model_id)


def _extract_names(items: list[object]) -> list[str]:
    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("model") or item.get("name")
            if model_id:
                names.append(str(model_id))
        else:
            names.append(str(item))
    return names


def load_observed(args: argparse.Namespace) -> list[str]:
    observed = list(args.observed_model)
    if not args.observed_json:
        return sorted({_normalize_model_id(item) for item in observed if item.strip()})

    payload = json.loads(Path(args.observed_json).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        observed.extend(_extract_names(payload))
    elif isinstance(payload, dict):
        for key in ("models", "observed", "items", "model_ids", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                observed.extend(_extract_names(value))
                break
    else:
        raise ValueError("observed JSON must be a list or object")
    return sorted({_normalize_model_id(item) for item in observed if item.strip()})


def main() -> int:
    args = parse_args()
    observed = load_observed(args)
    expected = set(CANONICAL_MATRIX.values())
    observed_set = set(observed)

    missing = sorted(expected - observed_set)
    extra = sorted(observed_set - expected)
    report = ModelMatrixReport(
        canonical=CANONICAL_MATRIX,
        observed=observed,
        missing=missing,
        extra=extra,
    )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if not observed:
        print("matrix: canonical set loaded")
        for role, model in CANONICAL_MATRIX.items():
            print(f"{role}={model}")
        return 0

    print(f"matrix: observed={len(observed)} missing={len(missing)} extra={len(extra)}")
    for item in missing:
        print(f"missing:{item}")
    for item in extra:
        print(f"extra:{item}")
    return 0 if not missing and not extra else 1


if __name__ == "__main__":
    raise SystemExit(main())
