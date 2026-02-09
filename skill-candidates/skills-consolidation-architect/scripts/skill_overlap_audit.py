#!/usr/bin/env python3
"""Audit overlap across SKILL.md files to support modular consolidation."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

STOPWORDS = {
    "the",
    "and",
    "to",
    "of",
    "in",
    "for",
    "with",
    "or",
    "a",
    "an",
    "is",
    "are",
    "when",
    "use",
    "this",
    "skill",
    "run",
    "from",
}


@dataclass
class SkillDoc:
    name: str
    path: Path
    text: str
    token_set: set[str]


@dataclass
class PairScore:
    left: str
    right: str
    score: float
    jaccard: float
    sequence: float

    def level(self) -> str:
        if self.score >= 0.55:
            return "merge_candidate"
        if self.score >= 0.35:
            return "boundary_blur"
        return "distinct"


def parse_args() -> argparse.Namespace:
    default_skills_root = str(Path(os.environ.get("CODEX_HOME", "~/.codex")) / "skills")
    parser = argparse.ArgumentParser(description="Audit SKILL.md overlap")
    parser.add_argument(
        "--skills-root",
        default=default_skills_root,
        help="Root directory containing installed skills",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.28,
        help="Minimum score to include in pair output",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write JSON report",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include .system skills",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    """Strip fenced code blocks to focus on instructional overlap."""

    return re.sub(r"```[\s\S]*?```", "", text)


def token_set(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9_\-/]+", text.lower())
    return {tok for tok in tokens if tok not in STOPWORDS and len(tok) > 2}


def load_skill_docs(skills_root: Path, include_system: bool) -> list[SkillDoc]:
    docs: list[SkillDoc] = []
    for entry in sorted(skills_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name == ".system" and not include_system:
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        raw = skill_md.read_text(encoding="utf-8", errors="ignore")
        cleaned = normalize_text(raw)
        docs.append(
            SkillDoc(
                name=entry.name,
                path=skill_md,
                text=cleaned,
                token_set=token_set(cleaned),
            )
        )
    return docs


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def build_pair_scores(docs: list[SkillDoc]) -> list[PairScore]:
    pairs: list[PairScore] = []
    for index, left in enumerate(docs):
        for right in docs[index + 1 :]:
            jac = jaccard(left.token_set, right.token_set)
            seq = SequenceMatcher(None, left.text, right.text).ratio()
            score = (jac * 0.55) + (seq * 0.45)
            pairs.append(
                PairScore(
                    left=left.name,
                    right=right.name,
                    score=score,
                    jaccard=jac,
                    sequence=seq,
                )
            )
    return sorted(pairs, key=lambda item: item.score, reverse=True)


def infer_group(name: str) -> str:
    for prefix in (
        "repo-b",
        "repo-a",
        "repo-c",
        "repo-d",
        "skill-arbiter",
        "skills",
        "repo_b-dfp",
    ):
        if name.startswith(prefix):
            return prefix
    return "other"


def group_counts(docs: Iterable[SkillDoc]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for doc in docs:
        group = infer_group(doc.name)
        counts[group] = counts.get(group, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    args = parse_args()
    root = Path(args.skills_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"error: skills root not found: {root}")

    docs = load_skill_docs(root, args.include_system)
    pairs = build_pair_scores(docs)
    filtered = [pair for pair in pairs if pair.score >= args.threshold]
    max_pair = pairs[0] if pairs else None

    payload = {
        "skills_root": str(root),
        "skills_scanned": len(docs),
        "group_counts": group_counts(docs),
        "threshold": args.threshold,
        "max_pair": None
        if max_pair is None
        else {
            "left": max_pair.left,
            "right": max_pair.right,
            "score": round(max_pair.score, 3),
            "jaccard": round(max_pair.jaccard, 3),
            "sequence": round(max_pair.sequence, 3),
            "level": max_pair.level(),
        },
        "pairs": [
            {
                "left": pair.left,
                "right": pair.right,
                "score": round(pair.score, 3),
                "jaccard": round(pair.jaccard, 3),
                "sequence": round(pair.sequence, 3),
                "level": pair.level(),
            }
            for pair in filtered
        ],
    }

    print(f"skills_scanned={payload['skills_scanned']}")
    print(f"group_counts={payload['group_counts']}")
    if payload["max_pair"]:
        max_info = payload["max_pair"]
        print(
            "max_pair="
            f"{max_info['left']}<->{max_info['right']} "
            f"score={max_info['score']} level={max_info['level']}"
        )
    else:
        print("max_pair=none")
    print(f"pairs_at_or_above_threshold={len(payload['pairs'])}")

    if args.json_out:
        out_path = Path(args.json_out).expanduser()
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
