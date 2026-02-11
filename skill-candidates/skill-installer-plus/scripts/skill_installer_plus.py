#!/usr/bin/env python3
"""Local-first skill installer with lockdown admission and learning loop."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

DEFAULT_LEDGER = Path.home() / ".codex" / "skills" / ".skill-installer-plus-ledger.json"
DEFAULT_DEST = Path.home() / ".codex" / "skills"
DEFAULT_BLACKLIST = ".blacklist.local"
DEFAULT_WHITELIST = ".whitelist.local"

SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

MANUAL_EVENT_WEIGHTS = {
    "success": 4,
    "warn": -5,
    "failure": -10,
    "disabled": -16,
    "quarantined": -18,
    "restored": 8,
}

TIER_BONUS = {
    "trusted": 20,
    "observe": 8,
    "restricted": -12,
    "blocked": -30,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Skill installer with recommendation feedback loop")
    parser.add_argument(
        "--ledger",
        default=str(DEFAULT_LEDGER),
        help="Installer ledger JSON path",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Build ranked install recommendations")
    plan.add_argument("--skills-root", default="skill-candidates", help="Local skill candidates root")
    plan.add_argument("--skill", action="append", default=[], help="Specific skill to include (repeatable)")
    plan.add_argument("--dest", default=str(DEFAULT_DEST), help="Skills destination root")
    plan.add_argument("--blacklist", default=DEFAULT_BLACKLIST, help="Blacklist filename under --dest")
    plan.add_argument("--whitelist", default=DEFAULT_WHITELIST, help="Whitelist filename under --dest")
    plan.add_argument("--trust-report", default="", help="Optional trust-ledger report JSON path")
    plan.add_argument("--json-out", default="", help="Optional JSON report path")
    plan.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    admit = subparsers.add_parser("admit", help="Run lockdown admission and update learning ledger")
    admit.add_argument("--skill", action="append", default=[], help="Skill name to admit (repeatable)")
    admit.add_argument("--skills-file", default="", help="Optional newline-delimited skill list file")
    admit.add_argument("--source-dir", default="skill-candidates", help="Local source dir for skill candidates")
    admit.add_argument("--dest", default=str(DEFAULT_DEST), help="Skills destination root")
    admit.add_argument("--window", type=int, default=10, help="Arbiter sample window")
    admit.add_argument("--baseline-window", type=int, default=3, help="Arbiter baseline window")
    admit.add_argument("--threshold", type=int, default=3, help="Arbiter persistence threshold")
    admit.add_argument("--max-rg", type=int, default=3, help="Arbiter max-rg threshold")
    admit.add_argument("--arbiter-script", default="", help="Path to arbitrate_skills.py")
    admit.add_argument("--arbiter-json", default="", help="Path for arbiter --json-out output")
    admit.add_argument("--dry-run", action="store_true", help="Pass --dry-run to arbiter")
    admit.add_argument(
        "--ingest-trust-ledger",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ingest arbiter report into trust ledger after a non-dry-run pass",
    )
    admit.add_argument("--trust-ledger-script", default="", help="Path to trust_ledger.py")
    admit.add_argument(
        "--trust-ledger",
        default=str(Path.home() / ".codex" / "skills" / ".trust-ledger.local.json"),
        help="Trust ledger path when ingesting arbiter results",
    )
    admit.add_argument("--trust-json-out", default="", help="Optional JSON path for trust ingest output")
    admit.add_argument("--json-out", default="", help="Optional installer admit summary JSON output")
    admit.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    feedback = subparsers.add_parser("feedback", help="Record manual post-install feedback")
    feedback.add_argument("--skill", required=True, help="Skill name")
    feedback.add_argument(
        "--event",
        required=True,
        choices=tuple(sorted(MANUAL_EVENT_WEIGHTS)),
        help="Feedback event type",
    )
    feedback.add_argument("--note", default="", help="Optional note")
    feedback.add_argument("--json-out", default="", help="Optional JSON output path")
    feedback.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    show = subparsers.add_parser("show", help="Display installer ledger status")
    show.add_argument("--recent", type=int, default=6, help="Number of recent events to display")
    show.add_argument("--json-out", default="", help="Optional JSON output path")
    show.add_argument("--format", choices=("table", "json"), default="table", help="Console output format")

    return parser.parse_args()


def write_json(path_text: str, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return payload


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "updated_at": now_iso(), "profiles": {}, "events": []}
    payload = load_json_object(path)
    if not isinstance(payload.get("profiles"), dict):
        payload["profiles"] = {}
    if not isinstance(payload.get("events"), list):
        payload["events"] = []
    if "version" not in payload:
        payload["version"] = 1
    if "updated_at" not in payload:
        payload["updated_at"] = now_iso()
    return payload


def save_ledger(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def normalize_skill(name: str) -> str:
    value = str(name or "").strip()
    if not value:
        raise ValueError("empty skill name")
    if not SKILL_NAME_RE.fullmatch(value):
        raise ValueError(f"invalid skill name: {value!r}")
    return value


def normalize_skills(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        value = normalize_skill(raw)
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def collect_skills(cli_skills: list[str], skills_file: str) -> list[str]:
    values: list[str] = []
    values.extend(cli_skills)
    if skills_file:
        path = Path(skills_file).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"--skills-file not found: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            values.append(text)
    if not values:
        raise ValueError("no skills provided; use --skill and/or --skills-file")
    return normalize_skills(values)


def load_name_file(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            out.add(normalize_skill(text))
        except ValueError:
            continue
    return out


def skill_dirs(root: Path, selected: set[str]) -> dict[str, Path]:
    if not root.is_dir():
        raise ValueError(f"skills root not found: {root}")
    out: dict[str, Path] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        if selected and child.name not in selected:
            continue
        if (child / "SKILL.md").is_file():
            out[child.name] = child
    return out


def trust_map(path_text: str) -> dict[str, dict[str, Any]]:
    if not path_text:
        return {}
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"trust report not found: {path}")
    payload = load_json_object(path)
    rows = payload.get("skills")
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill") or "").strip()
        if not skill:
            continue
        out[skill] = {
            "tier": str(item.get("tier") or "").strip().lower(),
            "score": int(item.get("score") or 0),
        }
    return out


def ensure_profile(ledger: dict[str, Any], skill: str) -> dict[str, Any]:
    profiles = ledger.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("ledger profiles must be an object")
    row = profiles.get(skill)
    if not isinstance(row, dict):
        row = {
            "arbiter_runs": 0,
            "kept": 0,
            "deleted": 0,
            "persistent_hits": 0,
            "max_rg_history": [],
            "manual_events": {},
            "last_action": "",
            "last_note": "",
            "updated_at": now_iso(),
        }
        profiles[skill] = row
    if not isinstance(row.get("max_rg_history"), list):
        row["max_rg_history"] = []
    if not isinstance(row.get("manual_events"), dict):
        row["manual_events"] = {}
    for key in ("arbiter_runs", "kept", "deleted", "persistent_hits"):
        if not isinstance(row.get(key), int):
            row[key] = 0
    if not isinstance(row.get("last_action"), str):
        row["last_action"] = ""
    if not isinstance(row.get("last_note"), str):
        row["last_note"] = ""
    if not isinstance(row.get("updated_at"), str):
        row["updated_at"] = now_iso()
    return row


def manual_score(profile: dict[str, Any]) -> int:
    events = profile.get("manual_events")
    if not isinstance(events, dict):
        return 0
    score = 0
    for key, count in events.items():
        try:
            value = int(count)
        except (TypeError, ValueError):
            continue
        score += MANUAL_EVENT_WEIGHTS.get(str(key), 0) * value
    return score


def profile_metrics(profile: dict[str, Any]) -> dict[str, Any]:
    runs = int(profile.get("arbiter_runs") or 0)
    kept = int(profile.get("kept") or 0)
    deleted = int(profile.get("deleted") or 0)
    persistent_hits = int(profile.get("persistent_hits") or 0)
    history = profile.get("max_rg_history")
    if not isinstance(history, list):
        history = []
    values: list[int] = []
    for raw in history:
        try:
            values.append(max(int(raw), 0))
        except (TypeError, ValueError):
            continue
    avg_max_rg = (sum(values) / len(values)) if values else 0.0
    pass_rate = (kept / runs) if runs > 0 else 0.0
    return {
        "runs": runs,
        "kept": kept,
        "deleted": deleted,
        "persistent_hits": persistent_hits,
        "avg_max_rg": avg_max_rg,
        "pass_rate": pass_rate,
        "manual_score": manual_score(profile),
    }


def score_recommendation(
    metrics: dict[str, Any],
    trust_tier: str,
    *,
    blacklisted: bool,
    whitelisted: bool,
) -> tuple[int, str]:
    score = 45
    runs = int(metrics["runs"])
    if runs == 0:
        score += 5
    else:
        score += int(round(float(metrics["pass_rate"]) * 30.0))
        score += int(metrics["kept"]) * 3
        score -= int(metrics["deleted"]) * 4
        score -= int(metrics["persistent_hits"]) * 10
        score -= int(round(float(metrics["avg_max_rg"]) * 8.0))
    score += int(metrics["manual_score"])
    score += TIER_BONUS.get(trust_tier, 0)
    if whitelisted:
        score += 10
    if blacklisted:
        score -= 80

    decision = "defer"
    if blacklisted or trust_tier == "blocked":
        decision = "blocked"
    elif score >= 70:
        decision = "install"
    elif score >= 50:
        decision = "review"
    elif score < 20:
        decision = "blocked"
    return score, decision


def resolve_repo_root_from_script(script_path: Path) -> Path | None:
    for parent in script_path.parents:
        candidate = parent / "scripts" / "arbitrate_skills.py"
        if candidate.is_file():
            return parent
    return None


def resolve_arbiter_script(explicit: str) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())

    env_value = os.environ.get("SKILL_ARBITER_SCRIPT", "").strip()
    if env_value:
        candidates.append(Path(env_value).expanduser().resolve())

    local_repo = resolve_repo_root_from_script(Path(__file__).resolve())
    if local_repo is not None:
        candidates.append(local_repo / "scripts" / "arbitrate_skills.py")

    candidates.append(Path.home() / ".codex" / "skills" / "skill-arbiter" / "scripts" / "arbitrate_skills.py")
    for path in candidates:
        if path.is_file():
            return path
    attempted = ", ".join(str(path) for path in candidates)
    raise ValueError(f"could not resolve arbitrate_skills.py; checked: {attempted}")


def resolve_trust_ledger_script(explicit: str) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser().resolve())

    env_value = os.environ.get("SKILL_TRUST_LEDGER_SCRIPT", "").strip()
    if env_value:
        candidates.append(Path(env_value).expanduser().resolve())

    local_repo = resolve_repo_root_from_script(Path(__file__).resolve())
    if local_repo is not None:
        candidates.append(
            local_repo / "skill-candidates" / "skill-trust-ledger" / "scripts" / "trust_ledger.py"
        )

    candidates.append(
        Path.home() / ".codex" / "skills" / "skill-trust-ledger" / "scripts" / "trust_ledger.py"
    )
    for path in candidates:
        if path.is_file():
            return path
    attempted = ", ".join(str(path) for path in candidates)
    raise ValueError(f"could not resolve trust_ledger.py; checked: {attempted}")


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def apply_arbiter_result(profile: dict[str, Any], row: dict[str, Any]) -> None:
    action = str(row.get("action") or "").strip().lower()
    note = str(row.get("note") or "").strip()
    max_rg_raw = row.get("max_rg")
    try:
        max_rg = max(int(max_rg_raw), 0)
    except (TypeError, ValueError):
        max_rg = 0
    persistent = bool(row.get("persistent_nonzero"))

    profile["arbiter_runs"] = int(profile.get("arbiter_runs") or 0) + 1
    if action in {"kept", "promoted"}:
        profile["kept"] = int(profile.get("kept") or 0) + 1
    elif action in {"deleted", "blacklisted", "quarantined"}:
        profile["deleted"] = int(profile.get("deleted") or 0) + 1
    if persistent:
        profile["persistent_hits"] = int(profile.get("persistent_hits") or 0) + 1

    history = profile.get("max_rg_history")
    if not isinstance(history, list):
        history = []
        profile["max_rg_history"] = history
    history.append(max_rg)
    if len(history) > 50:
        del history[:-50]

    profile["last_action"] = action
    profile["last_note"] = note
    profile["updated_at"] = now_iso()


def run_plan(args: argparse.Namespace, ledger_path: Path) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    selected = set(normalize_skills(args.skill)) if args.skill else set()
    root = Path(args.skills_root).expanduser().resolve()
    found = skill_dirs(root, selected)
    if not found:
        raise ValueError("no matching skills found")

    trust = trust_map(args.trust_report)
    dest = Path(args.dest).expanduser().resolve()
    blacklist = load_name_file(dest / args.blacklist)
    whitelist = load_name_file(dest / args.whitelist)

    profiles = ledger.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    rows: list[dict[str, Any]] = []
    for skill in sorted(found):
        profile = profiles.get(skill) if isinstance(profiles.get(skill), dict) else {}
        metrics = profile_metrics(profile if isinstance(profile, dict) else {})
        trust_row = trust.get(skill, {})
        tier = str(trust_row.get("tier") or "")
        blacklisted = skill in blacklist
        whitelisted = skill in whitelist
        score, decision = score_recommendation(
            metrics,
            tier,
            blacklisted=blacklisted,
            whitelisted=whitelisted,
        )
        rows.append(
            {
                "skill": skill,
                "score": score,
                "decision": decision,
                "trust_tier": tier or "unknown",
                "trust_score": int(trust_row.get("score") or 0) if trust_row else 0,
                "blacklisted": blacklisted,
                "whitelisted": whitelisted,
                "arbiter_runs": int(metrics["runs"]),
                "kept": int(metrics["kept"]),
                "deleted": int(metrics["deleted"]),
                "persistent_hits": int(metrics["persistent_hits"]),
                "avg_max_rg": round(float(metrics["avg_max_rg"]), 3),
                "pass_rate": round(float(metrics["pass_rate"]), 3),
                "manual_score": int(metrics["manual_score"]),
            }
        )

    rows.sort(key=lambda item: (-int(item["score"]), item["skill"]))
    recommendations: list[str] = []
    if any(item["decision"] == "install" for item in rows):
        recommendations.append("Admit top 'install' rows first using personal-lockdown mode.")
    if any(item["decision"] == "review" for item in rows):
        recommendations.append("Review medium-confidence rows before admission.")
    if any(item["decision"] == "blocked" for item in rows):
        recommendations.append("Keep blocked rows disabled until fresh evidence is collected.")
    if not recommendations:
        recommendations.append("No candidate exceeded current install threshold.")

    return {
        "generated_at": now_iso(),
        "command": "plan",
        "skills_root": str(root),
        "dest": str(dest),
        "ledger": str(ledger_path),
        "skills": rows,
        "recommendations": recommendations,
    }


def run_admit(args: argparse.Namespace, ledger_path: Path) -> dict[str, Any]:
    skills = collect_skills(args.skill, args.skills_file)
    source_dir = Path(args.source_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise ValueError(f"--source-dir not found: {source_dir}")
    dest = Path(args.dest).expanduser().resolve()
    arbiter_script = resolve_arbiter_script(args.arbiter_script)

    if args.arbiter_json:
        arbiter_json = Path(args.arbiter_json).expanduser().resolve()
    else:
        tmp = tempfile.NamedTemporaryFile(
            prefix="skill-installer-plus-arbiter-",
            suffix=".json",
            delete=False,
        )
        tmp.close()
        arbiter_json = Path(tmp.name)

    cmd = [
        sys.executable,
        str(arbiter_script),
        *skills,
        "--source-dir",
        str(source_dir),
        "--dest",
        str(dest),
        "--window",
        str(int(args.window)),
        "--baseline-window",
        str(int(args.baseline_window)),
        "--threshold",
        str(int(args.threshold)),
        "--max-rg",
        str(int(args.max_rg)),
        "--personal-lockdown",
        "--json-out",
        str(arbiter_json),
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    proc = run_command(cmd)
    if proc.returncode != 0:
        detail = {
            "generated_at": now_iso(),
            "command": "admit",
            "status": "failed",
            "arbiter_command": cmd,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
        return detail

    payload = load_json_object(arbiter_json)
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise ValueError(f"arbiter results[] missing in {arbiter_json}")

    updated_profiles: list[dict[str, Any]] = []
    if not args.dry_run:
        ledger = load_ledger(ledger_path)
        for item in rows:
            if not isinstance(item, dict):
                continue
            skill = str(item.get("skill") or "").strip()
            if not skill:
                continue
            profile = ensure_profile(ledger, skill)
            apply_arbiter_result(profile, item)
            metrics = profile_metrics(profile)
            updated_profiles.append(
                {
                    "skill": skill,
                    "runs": int(metrics["runs"]),
                    "kept": int(metrics["kept"]),
                    "deleted": int(metrics["deleted"]),
                    "pass_rate": round(float(metrics["pass_rate"]), 3),
                }
            )
        events = ledger.setdefault("events", [])
        if not isinstance(events, list):
            events = []
            ledger["events"] = events
        events.append(
            {
                "timestamp": now_iso(),
                "type": "admit",
                "skills": skills,
                "dry_run": False,
                "arbiter_report": str(arbiter_json),
                "results": [
                    {
                        "skill": str(item.get("skill") or ""),
                        "action": str(item.get("action") or ""),
                        "max_rg": int(item.get("max_rg") or 0) if isinstance(item, dict) else 0,
                        "persistent_nonzero": bool(item.get("persistent_nonzero")) if isinstance(item, dict) else False,
                    }
                    for item in rows
                    if isinstance(item, dict)
                ],
            }
        )
        if len(events) > 200:
            del events[:-200]
        save_ledger(ledger_path, ledger)

    trust_ingest: dict[str, Any] = {
        "status": "skipped",
        "reason": "disabled or dry-run",
    }
    if args.ingest_trust_ledger and not args.dry_run:
        try:
            trust_script = resolve_trust_ledger_script(args.trust_ledger_script)
            trust_cmd = [
                sys.executable,
                str(trust_script),
                "--ledger",
                str(Path(args.trust_ledger).expanduser().resolve()),
                "ingest-arbiter",
                "--input",
                str(arbiter_json),
            ]
            if args.trust_json_out:
                trust_cmd.extend(["--json-out", str(Path(args.trust_json_out).expanduser().resolve())])
            trust_proc = run_command(trust_cmd)
            trust_ingest = {
                "status": "ok" if trust_proc.returncode == 0 else "failed",
                "script": str(trust_script),
                "returncode": trust_proc.returncode,
                "stdout": trust_proc.stdout.strip(),
                "stderr": trust_proc.stderr.strip(),
            }
        except ValueError as exc:
            trust_ingest = {"status": "skipped", "reason": str(exc)}

    result = {
        "generated_at": now_iso(),
        "command": "admit",
        "status": "ok",
        "dry_run": bool(args.dry_run),
        "skills": skills,
        "source_dir": str(source_dir),
        "dest": str(dest),
        "ledger": str(ledger_path),
        "arbiter_script": str(arbiter_script),
        "arbiter_report": str(arbiter_json),
        "arbiter_returncode": proc.returncode,
        "arbiter_stdout": proc.stdout.strip(),
        "arbiter_stderr": proc.stderr.strip(),
        "results": rows,
        "updated_profiles": updated_profiles,
        "trust_ingest": trust_ingest,
    }

    return result


def run_feedback(args: argparse.Namespace, ledger_path: Path) -> dict[str, Any]:
    skill = normalize_skill(args.skill)
    event = str(args.event).strip().lower()
    note = str(args.note or "").strip()

    ledger = load_ledger(ledger_path)
    profile = ensure_profile(ledger, skill)
    manual = profile.setdefault("manual_events", {})
    if not isinstance(manual, dict):
        manual = {}
        profile["manual_events"] = manual
    manual[event] = int(manual.get(event) or 0) + 1
    profile["updated_at"] = now_iso()

    events = ledger.setdefault("events", [])
    if not isinstance(events, list):
        events = []
        ledger["events"] = events
    events.append(
        {
            "timestamp": now_iso(),
            "type": "feedback",
            "skill": skill,
            "event": event,
            "note": note,
        }
    )
    if len(events) > 200:
        del events[:-200]

    save_ledger(ledger_path, ledger)
    metrics = profile_metrics(profile)
    score, decision = score_recommendation(
        metrics,
        trust_tier="",
        blacklisted=False,
        whitelisted=False,
    )
    return {
        "generated_at": now_iso(),
        "command": "feedback",
        "ledger": str(ledger_path),
        "skill": skill,
        "event": event,
        "note": note,
        "manual_events": dict(sorted((str(k), int(v)) for k, v in manual.items())),
        "updated_score": score,
        "updated_decision": decision,
    }


def run_show(args: argparse.Namespace, ledger_path: Path) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    profiles = ledger.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}

    rows: list[dict[str, Any]] = []
    for skill, profile_raw in profiles.items():
        if not isinstance(profile_raw, dict):
            continue
        try:
            name = normalize_skill(skill)
        except ValueError:
            continue
        metrics = profile_metrics(profile_raw)
        score, decision = score_recommendation(
            metrics,
            trust_tier="",
            blacklisted=False,
            whitelisted=False,
        )
        rows.append(
            {
                "skill": name,
                "score": score,
                "decision": decision,
                "runs": int(metrics["runs"]),
                "kept": int(metrics["kept"]),
                "deleted": int(metrics["deleted"]),
                "persistent_hits": int(metrics["persistent_hits"]),
                "avg_max_rg": round(float(metrics["avg_max_rg"]), 3),
                "pass_rate": round(float(metrics["pass_rate"]), 3),
                "manual_score": int(metrics["manual_score"]),
            }
        )
    rows.sort(key=lambda item: (-int(item["score"]), item["skill"]))

    recent = max(int(args.recent), 0)
    events_raw = ledger.get("events")
    recent_events: list[dict[str, Any]] = []
    if isinstance(events_raw, list) and recent > 0:
        for item in events_raw[-recent:]:
            if isinstance(item, dict):
                recent_events.append(item)

    return {
        "generated_at": now_iso(),
        "command": "show",
        "ledger": str(ledger_path),
        "profiles": rows,
        "recent_events": recent_events,
    }


def render_plan_table(payload: dict[str, Any]) -> str:
    lines = [
        f"skills_root: {payload['skills_root']}",
        f"ledger: {payload['ledger']}",
        "",
        "skill                              decision  score  tier        runs  kept  del  max_rg  pass",
        "---------------------------------  --------  -----  ----------  ----  ----  ---  ------  -----",
    ]
    for row in payload.get("skills", []):
        lines.append(
            "{skill:<33}  {decision:<8}  {score:>5}  {tier:<10}  {runs:>4}  {kept:>4}  {deleted:>3}  {avg:>6}  {pass_rate:>5}".format(
                skill=str(row.get("skill", ""))[:33],
                decision=str(row.get("decision", "")),
                score=int(row.get("score", 0)),
                tier=str(row.get("trust_tier", "unknown")),
                runs=int(row.get("arbiter_runs", 0)),
                kept=int(row.get("kept", 0)),
                deleted=int(row.get("deleted", 0)),
                avg=f"{float(row.get('avg_max_rg', 0.0)):.2f}",
                pass_rate=f"{float(row.get('pass_rate', 0.0)):.2f}",
            )
        )
    lines.append("")
    lines.append("recommendations:")
    for text in payload.get("recommendations", []):
        lines.append(f"- {text}")
    return "\n".join(lines)


def render_admit_table(payload: dict[str, Any]) -> str:
    if payload.get("status") != "ok":
        return (
            "admit failed:\n"
            f"returncode={payload.get('returncode', payload.get('arbiter_returncode', 1))}\n"
            f"stderr={payload.get('stderr', payload.get('arbiter_stderr', '')).strip()}"
        )
    lines = [
        f"arbiter_report: {payload.get('arbiter_report', '')}",
        f"ledger: {payload.get('ledger', '')}",
        f"dry_run: {str(bool(payload.get('dry_run', False))).lower()}",
        "",
        "skill                              action      max_rg  persistent",
        "---------------------------------  ----------  ------  ----------",
    ]
    for row in payload.get("results", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "{skill:<33}  {action:<10}  {max_rg:>6}  {persistent:<10}".format(
                skill=str(row.get("skill", ""))[:33],
                action=str(row.get("action", "")),
                max_rg=int(row.get("max_rg", 0)),
                persistent=str(bool(row.get("persistent_nonzero", False))).lower(),
            )
        )
    trust = payload.get("trust_ingest", {})
    if isinstance(trust, dict):
        lines.append("")
        lines.append(f"trust_ingest: {trust.get('status', 'unknown')}")
        reason = str(trust.get("reason", "")).strip()
        if reason:
            lines.append(f"trust_reason: {reason}")
    return "\n".join(lines)


def render_feedback_table(payload: dict[str, Any]) -> str:
    return (
        f"recorded: skill={payload['skill']} event={payload['event']} "
        f"score={payload['updated_score']} decision={payload['updated_decision']}"
    )


def render_show_table(payload: dict[str, Any]) -> str:
    lines = [
        f"ledger: {payload['ledger']}",
        "",
        "skill                              score  decision  runs  kept  del  max_rg  pass",
        "---------------------------------  -----  --------  ----  ----  ---  ------  -----",
    ]
    for row in payload.get("profiles", []):
        lines.append(
            "{skill:<33}  {score:>5}  {decision:<8}  {runs:>4}  {kept:>4}  {deleted:>3}  {avg:>6}  {pass_rate:>5}".format(
                skill=str(row.get("skill", ""))[:33],
                score=int(row.get("score", 0)),
                decision=str(row.get("decision", "")),
                runs=int(row.get("runs", 0)),
                kept=int(row.get("kept", 0)),
                deleted=int(row.get("deleted", 0)),
                avg=f"{float(row.get('avg_max_rg', 0.0)):.2f}",
                pass_rate=f"{float(row.get('pass_rate', 0.0)):.2f}",
            )
        )
    lines.append("")
    lines.append("recent_events:")
    for item in payload.get("recent_events", []):
        if not isinstance(item, dict):
            continue
        stamp = str(item.get("timestamp", ""))
        typ = str(item.get("type", ""))
        skill = str(item.get("skill", ""))
        lines.append(f"- {stamp} type={typ} skill={skill}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    ledger_path = Path(args.ledger).expanduser().resolve()
    try:
        if args.command == "plan":
            payload = run_plan(args, ledger_path)
        elif args.command == "admit":
            payload = run_admit(args, ledger_path)
            if payload.get("status") != "ok":
                write_json(args.json_out, payload)
                if args.format == "json":
                    print(json.dumps(payload, indent=2, ensure_ascii=True))
                else:
                    print(render_admit_table(payload))
                return int(payload.get("returncode", payload.get("arbiter_returncode", 1)) or 1)
        elif args.command == "feedback":
            payload = run_feedback(args, ledger_path)
        elif args.command == "show":
            payload = run_show(args, ledger_path)
        else:
            raise ValueError(f"unsupported command: {args.command}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    write_json(args.json_out, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        if args.command == "plan":
            print(render_plan_table(payload))
        elif args.command == "admit":
            print(render_admit_table(payload))
        elif args.command == "feedback":
            print(render_feedback_table(payload))
        else:
            print(render_show_table(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
