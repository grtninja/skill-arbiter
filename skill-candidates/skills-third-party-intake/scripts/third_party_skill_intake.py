#!/usr/bin/env python3
"""Scan third-party skill catalogs and emit deterministic intake recommendations."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

MAX_READ_BYTES = 512 * 1024
SCRIPT_SUFFIXES = (".sh", ".bash", ".zsh", ".ksh", ".fish", ".ps1", ".bat", ".cmd")
MARKDOWN_SUFFIXES = (".md", ".markdown")
SENSITIVE_MARKERS = (
    "token",
    "secret",
    "api_key",
    "apikey",
    "password",
    "oauth",
    "discord",
    "telegram",
    "imessage",
    "slack",
)
HIGH_RISK_PATTERNS = (
    r"curl\s+[^|\n\r]+?\|\s*(?:sh|bash|zsh)\b",
    r"wget\s+[^|\n\r]+?\|\s*(?:sh|bash|zsh)\b",
    r"\binvoke-expression\b",
    r"(?<![A-Za-z0-9_])iex(?![A-Za-z0-9_])",
    r"rm\s+-rf\s+/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\{:\|:&\};:",
    r"\bnc(?:at)?\b[^\n\r]*\s-e\s",
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_SPLIT_RE = re.compile(r"\r?\n")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = FRONTMATTER_SPLIT_RE.split(text)
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, text
    end = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end < 0:
        return {}, text
    out: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip().lower()] = value.strip().strip('"').strip("'")
    body = "\n".join(lines[end + 1 :])
    return out, body


def read_text(path: Path, *, max_bytes: int = MAX_READ_BYTES) -> str:
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(f"file exceeds size limit ({max_bytes} bytes): {path}")
    return data.decode("utf-8", errors="replace")


def has_shell_shebang(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:128]
    except OSError:
        return False
    if not chunk.startswith(b"#!"):
        return False
    lowered = chunk.decode("utf-8", errors="ignore").lower()
    return any(item in lowered for item in ("sh", "bash", "zsh", "pwsh", "powershell"))


def detect_high_risk(content: str) -> list[str]:
    hits: list[str] = []
    lowered = content.lower()
    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def normalize_markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">") and len(target) >= 2:
        target = target[1:-1].strip()
    if not target:
        return target
    pieces = target.split()
    if not pieces:
        return ""
    return pieces[0]


def scheme_of(target: str) -> str:
    match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", target)
    return match.group(1).lower() if match else ""


def is_absolute_or_escape(target: str) -> bool:
    if not target:
        return False
    if target.startswith(("/", "\\", "~/", "..")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", target):
        return True
    norm = target.replace("\\", "/")
    return "/../" in f"/{norm}/" or norm.startswith("../")


def scan_markdown_links(skill_dir: Path, source_path: Path) -> tuple[list[str], list[Finding]]:
    unsafe_links: list[str] = []
    findings: list[Finding] = []
    for md in skill_dir.rglob("*"):
        if not md.is_file():
            continue
        if md.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        try:
            text = read_text(md)
        except (OSError, ValueError) as exc:
            findings.append(Finding("high", "markdown_read_failed", str(exc)))
            continue

        for match in MARKDOWN_LINK_RE.finditer(text):
            target_raw = match.group(1)
            target = normalize_markdown_target(target_raw)
            if not target or target.startswith("#"):
                continue

            scheme = scheme_of(target)
            if scheme:
                if scheme in ("http", "https", "mailto"):
                    if target.lower().endswith(MARKDOWN_SUFFIXES):
                        unsafe_links.append(target)
                        findings.append(
                            Finding(
                                "high",
                                "external_markdown_link",
                                f"{md.name} links to remote markdown: {target}",
                            )
                        )
                    continue
                unsafe_links.append(target)
                findings.append(
                    Finding("high", "unsupported_link_scheme", f"{md.name} uses scheme '{scheme}' in {target}")
                )
                continue

            stripped = target.split("#", 1)[0].split("?", 1)[0]
            if not stripped:
                continue
            if is_absolute_or_escape(stripped):
                unsafe_links.append(target)
                findings.append(Finding("high", "unsafe_path_link", f"{md.name} has unsafe local link: {target}"))
                continue
            if stripped.lower().endswith(SCRIPT_SUFFIXES):
                unsafe_links.append(target)
                findings.append(
                    Finding("high", "script_link_target", f"{md.name} links to script target: {target}")
                )
                continue
            if not stripped.lower().endswith(MARKDOWN_SUFFIXES):
                continue

            resolved = (md.parent / stripped).resolve()
            try:
                resolved.relative_to(source_path)
            except ValueError:
                unsafe_links.append(target)
                findings.append(
                    Finding("high", "link_escape_root", f"{md.name} link escapes source root: {target}")
                )
                continue
            if not resolved.is_file():
                unsafe_links.append(target)
                findings.append(Finding("medium", "link_missing_file", f"{md.name} link target missing: {target}"))

    return unsafe_links, findings


def gather_text_files(skill_dir: Path) -> list[Path]:
    out: list[Path] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        lowered = path.suffix.lower()
        if lowered in MARKDOWN_SUFFIXES or lowered in (".toml", ".txt", ".yaml", ".yml", ".json", ".py"):
            out.append(path)
    return out


def parse_source_arg(raw: str) -> tuple[str, Path]:
    text = raw.strip()
    if not text:
        raise ValueError("empty --source-root value")
    if "=" in text:
        label, path_text = text.split("=", 1)
        label = label.strip()
        path_text = path_text.strip()
        if not label:
            raise ValueError(f"invalid labeled source-root: {raw!r}")
        path = Path(path_text).expanduser().resolve()
        return label, path
    path = Path(text).expanduser().resolve()
    return path.name or "source", path


def normalize_skill_name(value: str) -> str:
    return value.strip().lower()


def summarize(source_label: str, source_root: Path, skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)
    metadata, body = parse_frontmatter(text)
    line_count = len(text.splitlines())

    findings: list[Finding] = []
    markers: set[str] = set()
    scripts: list[str] = []
    shebang_files: list[str] = []
    high_risk_hits: list[str] = []

    folder_name = skill_dir.name
    fm_name = metadata.get("name", "").strip()
    fm_description = metadata.get("description", "").strip()

    if not fm_name:
        findings.append(Finding("high", "frontmatter_name_missing", "frontmatter 'name' is missing"))
    if not fm_description:
        findings.append(Finding("high", "frontmatter_description_missing", "frontmatter 'description' is missing"))
    if fm_name and normalize_skill_name(fm_name) != normalize_skill_name(folder_name):
        findings.append(
            Finding(
                "medium",
                "frontmatter_name_mismatch",
                f"frontmatter name {fm_name!r} does not match folder {folder_name!r}",
            )
        )

    has_agents_openai = (skill_dir / "agents" / "openai.yaml").is_file()
    if not has_agents_openai:
        findings.append(Finding("medium", "agents_openai_missing", "agents/openai.yaml is missing"))

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(skill_dir)).replace("\\", "/")
        if path.suffix.lower() in SCRIPT_SUFFIXES:
            scripts.append(rel)
        if has_shell_shebang(path):
            shebang_files.append(rel)

    if scripts:
        findings.append(Finding("medium", "script_files_present", f"script files detected: {len(scripts)}"))
    if shebang_files:
        findings.append(Finding("high", "shell_shebang_detected", f"shell shebang files detected: {len(shebang_files)}"))

    unsafe_links, link_findings = scan_markdown_links(skill_dir, source_root)
    findings.extend(link_findings)

    scan_blob_parts: list[str] = [text, body]
    for file_path in gather_text_files(skill_dir):
        if file_path == skill_md:
            continue
        try:
            content = read_text(file_path)
        except (OSError, ValueError) as exc:
            findings.append(Finding("high", "file_read_failed", str(exc)))
            continue
        scan_blob_parts.append(content)
    scan_blob = "\n".join(scan_blob_parts)

    for marker in SENSITIVE_MARKERS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(marker)}(?![A-Za-z0-9_])", scan_blob, flags=re.IGNORECASE):
            markers.add(marker)

    if markers:
        findings.append(Finding("medium", "sensitive_markers", f"sensitive markers: {', '.join(sorted(markers))}"))

    high_risk_hits = detect_high_risk(scan_blob)
    if high_risk_hits:
        findings.append(Finding("high", "high_risk_snippet", f"high-risk patterns: {len(high_risk_hits)}"))

    compatibility = 1.0
    if not fm_name:
        compatibility -= 0.30
    if not fm_description:
        compatibility -= 0.20
    if not has_agents_openai:
        compatibility -= 0.15
    if scripts:
        compatibility -= 0.10
    compatibility = clamp(compatibility)

    quality = 0.60
    if 20 <= line_count <= 350:
        quality += 0.20
    if (skill_dir / "references").is_dir():
        quality += 0.10
    if (skill_dir / "scripts").is_dir():
        quality += 0.10
    if line_count < 10:
        quality -= 0.20
    if line_count > 500:
        quality -= 0.20
    if not fm_description:
        quality -= 0.20
    if not fm_name:
        quality -= 0.10
    quality = clamp(quality)

    security = 1.0
    if high_risk_hits:
        security -= 0.55
    if unsafe_links:
        security -= 0.35
    if shebang_files:
        security -= 0.35
    if scripts:
        security -= 0.20
    security -= min(len(markers), 3) * 0.15
    security = clamp(security)

    blockers = [f for f in findings if f.severity == "high"]
    warnings = [f for f in findings if f.severity == "medium"]
    score = clamp((compatibility * 0.35) + (quality * 0.30) + (security * 0.35))

    recommendation = "manual_review"
    if blockers:
        recommendation = "reject"
    elif security >= 0.75 and quality >= 0.55 and compatibility >= 0.60:
        recommendation = "admit"
    elif security < 0.55:
        recommendation = "reject"

    return {
        "source": source_label,
        "source_root": str(source_root),
        "skill": folder_name,
        "path": str(skill_dir),
        "frontmatter_name": fm_name,
        "description": fm_description,
        "line_count": line_count,
        "has_agents_openai": has_agents_openai,
        "script_files": sorted(scripts),
        "shebang_files": sorted(shebang_files),
        "unsafe_links": sorted(set(unsafe_links)),
        "sensitive_markers": sorted(markers),
        "high_risk_hits": high_risk_hits,
        "compatibility": round(compatibility, 4),
        "quality": round(quality, 4),
        "security": round(security, 4),
        "score": round(score, 4),
        "recommendation": recommendation,
        "findings": [
            {"severity": item.severity, "code": item.code, "message": item.message}
            for item in sorted(findings, key=lambda x: (x.severity, x.code, x.message))
        ],
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
    }


def discover_skill_dirs(source_root: Path) -> list[Path]:
    if not source_root.is_dir():
        raise ValueError(f"source root not found: {source_root}")
    out: list[Path] = []
    for path in source_root.rglob("SKILL.md"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        out.append(path.parent)
    return sorted(set(out), key=lambda p: str(p).lower())


def render_table(payload: dict[str, Any], min_security: float) -> str:
    lines: list[str] = []
    lines.append(f"generated_at: {payload['generated_at']}")
    lines.append(f"sources: {', '.join(payload['sources'])}")
    lines.append(f"skills_scanned: {payload['skills_scanned']}")
    lines.append(f"min_security: {min_security:.2f}")
    lines.append("")
    lines.append("recommendations:")
    for row in payload["skills"]:
        if row["security"] < min_security:
            continue
        lines.append(
            "- {skill} [{source}] => {rec} score={score:.2f} sec={sec:.2f} block={block} warn={warn}".format(
                skill=row["skill"],
                source=row["source"],
                rec=row["recommendation"],
                score=row["score"],
                sec=row["security"],
                block=row["blocker_count"],
                warn=row["warning_count"],
            )
        )
    if len(lines) == 6:
        lines.append("- none")
    lines.append("")
    counts = payload["summary"]
    lines.append(
        "summary: admit={admit} manual_review={manual_review} reject={reject}".format(
            admit=counts["admit"],
            manual_review=counts["manual_review"],
            reject=counts["reject"],
        )
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Third-party skill intake scanner")
    parser.add_argument(
        "--source-root",
        action="append",
        default=[],
        help="Path or label=path to scan (repeatable)",
    )
    parser.add_argument("--min-security", type=float, default=0.0, help="Display filter for table output")
    parser.add_argument("--json-out", default="", help="Optional JSON artifact path")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source_root:
        print("error: at least one --source-root is required", file=sys.stderr)
        return 2

    try:
        sources = [parse_source_arg(item) for item in args.source_root]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    try:
        for label, root in sources:
            for skill_dir in discover_skill_dirs(root):
                rows.append(summarize(label, root, skill_dir))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rows.sort(key=lambda row: (row["recommendation"], -row["score"], row["skill"]))
    summary = {
        "admit": sum(1 for row in rows if row["recommendation"] == "admit"),
        "manual_review": sum(1 for row in rows if row["recommendation"] == "manual_review"),
        "reject": sum(1 for row in rows if row["recommendation"] == "reject"),
    }
    payload = {
        "generated_at": now_iso(),
        "sources": [f"{label}={str(path)}" for label, path in sources],
        "skills_scanned": len(rows),
        "summary": summary,
        "skills": rows,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(render_table(payload, max(args.min_security, 0.0)))

    if args.json_out:
        path = Path(args.json_out).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
