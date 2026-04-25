from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .about import about_payload
from .meta_harness_policy import scan_candidate_meta_harness
from .paths import REPO_ROOT, host_id, public_readiness_cache_path, windows_no_window_subprocess_kwargs
from .privacy_policy import path_excluded_from_public_export, scan_repo
from .self_governance import run_self_governance_scan


REQUIRED_DOCS = [
    Path("AGENTS.md"),
    Path("README.md"),
    Path("BOUNDARIES.md"),
    Path("SECURITY.md"),
    Path("SUPPORT.md"),
    Path("CODE_OF_CONDUCT.md"),
    Path("CONTRIBUTING.md"),
    Path("SKILL.md"),
    Path("skill-catalog.md"),
    Path("docs/PROJECT_SCOPE.md"),
    Path("docs/SCOPE_TRACKER.md"),
    Path("references/skill-vetting-report.md"),
]
REQUIRED_ICON_ASSETS = [
    Path("apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.png"),
    Path("apps/nullclaw-desktop/assets/skill_arbiter_ntm_v4.ico"),
]
REQUIRED_LAUNCH_SURFACES = [
    Path("scripts/launch_security_console.vbs"),
]
REQUIRED_DOC_SNIPPETS = {
    Path("AGENTS.md"): [
        "G:\\GitHub",
        "http://127.0.0.1:9000/v1",
        "http://127.0.0.1:2337/v1",
        "Continue",
        "LM Studio",
        "local-agent",
        "operator surface",
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
    ],
    Path("BOUNDARIES.md"): [
        "G:\\GitHub",
        "http://127.0.0.1:9000/v1",
        "http://127.0.0.1:2337/v1",
        "Continue-facing local-agent surfaces",
        "No-stop doctrine",
        "Minimum runtime law",
        "reasoning visibility",
        "patience runtime window",
    ],
    Path("INSTRUCTIONS.md"): [
        "real local governance console",
        "minimum runtime law",
        "Continue-facing lanes",
        "visible action-state parity",
        "reasoning visibility",
        "patience runtime window",
    ],
    Path("CONTRIBUTING.md"): [
        "no-stop doctrine",
        "minimum runtime law",
        "visible action-state parity",
        "browser-tool or headless fallback surfaces",
        "reasoning visibility",
        "patience runtime window",
    ],
    Path("skill_arbiter/collaboration_support.py"): [
        "DEFAULT_TRUST_LEDGER",
        "trust_ledger",
        "ledger",
        "trust ledger",
    ],
}
README_REQUIRED_SNIPPETS = [
    "## Public support",
    "## Public release readiness",
    "## Safety and abuse handling",
    "## For humans",
    "## For AI agents",
    "## Local advisor",
    "## Quick start",
    "https://github.com/grtninja/skill-arbiter",
    "https://www.patreon.com/cw/grtninja",
]
SUSPICIOUS_TRACKED_PATTERNS = ("*.lnk", "*.jsonl", "*.sqlite", "*.sqlite3", "*.db", "*.pyc", "__pycache__/**")
UNSANITIZED_HOST_ID_RE = re.compile(r'(?m)(Host ID:\s*`(?!<LOCAL_HOST_ID>)[^`]+`|"host_id"\s*:\s*"(?!<LOCAL_HOST_ID>)[^"]+")')
SHELL_WRAPPED_DESKTOP_LAUNCH_RE = re.compile(
    r"powershell(?:\.exe)?\s+-ExecutionPolicy\s+Bypass\s+-File\s+\.\\scripts\\start_security_console\.ps1|"
    r"pwsh(?:\.exe)?\s+-ExecutionPolicy\s+Bypass\s+-File\s+\.\\scripts\\start_security_console\.ps1|"
    r"cmd(?:\.exe)?\s+/c[^\n\r]*start_security_console",
    re.IGNORECASE,
)
STALE_CONTINUE_BROWSER_HEADLESS_RE = re.compile(
    r"Continue[^\n\r]{0,160}(browser tools?|browser-tool|headless default|headless fallback|browser fallback)|"
    r"(browser tools?|browser-tool|headless default|headless fallback|browser fallback)[^\n\r]{0,160}Continue",
    re.IGNORECASE,
)
STALE_NO_STOP_MIN_RUNTIME_RE = re.compile(
    r"\b(no[- ]stop|minimum runtime)\b",
    re.IGNORECASE,
)
STALE_SELF_DIAGNOSIS_RE = re.compile(
    r"(stale session|degraded mode|waiting for a trigger|ask for a file path first)",
    re.IGNORECASE,
)
RG_COMMAND_INVOCATION_RE = re.compile(
    r"(?m)^[ \t]*(?:[^|\n\r]*\|\s*)?rg(?:\.exe)?\s+-",
    re.IGNORECASE,
)
MANDATORY_SKILL_CHAIN = (
    "skill-hub",
    "request-loopback-resume",
    "skill-common-sense-engineering",
    "usage-watcher",
    "skill-cost-credit-governor",
    "skill-trust-ledger",
)
MANDATORY_CODEX_PARITY = (
    "trusted folders",
    "local-subagent",
    "reasoning visibility",
    "visible action-state parity",
    "minimum runtime law",
    "no-stop doctrine",
)
CODEX_CONFIG_SKILL_BUNDLE = (
    "references/codex-config-self-maintenance.md",
    "skill-candidates/codex-config-self-maintenance/SKILL.md",
    "skill-candidates/codex-config-self-maintenance/references/config-contract.md",
    "skill-candidates/codex-config-self-maintenance/references/manifest-evidence.md",
    "skill-candidates/codex-config-self-maintenance/scripts/validate_candidate.py",
)
PRIVATE_PUBLISH_GUARD_TERMS_FILE = Path("skill_arbiter/private/publish_guard_terms.txt")
PUBLIC_CATALOG_SAFE_ADVISOR_NOTE = "_Live local advisor note omitted from public-shape catalog._"
PUBLISH_SURFACE_PREFIXES = ("skill_arbiter/", "scripts/", "skill-candidates/", "docs/", "references/", ".github/")
PUBLISH_SURFACE_FILES = {
    "AGENTS.md",
    "README.md",
    "BOUNDARIES.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SKILL.md",
    "CHANGELOG.md",
    "pyproject.toml",
}
PUBLIC_SHAPE_SCOPE_PREFIX_BLACKLIST = ("skill_arbiter/private/", "tests/private/")


def _finding(
    severity: str,
    code: str,
    summary: str,
    detail: str,
    recommended_action: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "summary": summary,
        "detail": detail,
        "recommended_action": recommended_action,
    }


def _run_git(repo_root: Path, *args: str):
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        **windows_no_window_subprocess_kwargs(),
    )


def _git_file_tracked(repo_root: Path, relative_path: str) -> bool:
    result = _run_git(repo_root, "ls-files", relative_path, f"{relative_path}/**")
    return bool(result.stdout.strip())


def _git_file_ignored(repo_root: Path, relative_path: str) -> bool:
    probes = [relative_path, f"{relative_path}/probe.tmp"]
    return any(_run_git(repo_root, "check-ignore", "-q", probe).returncode == 0 for probe in probes)


def _tracked_pattern_matches(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for pattern in SUSPICIOUS_TRACKED_PATTERNS:
        result = _run_git(repo_root, "ls-files", pattern)
        if result.returncode == 0:
            hits.extend([line.strip() for line in result.stdout.splitlines() if line.strip()])
    return sorted(set(hits))


def _unsanitized_host_id_hits(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".json", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if UNSANITIZED_HOST_ID_RE.search(text):
            hits.append(str(path.relative_to(repo_root)).replace("\\", "/"))
    return sorted(set(hits))


def _missing_required_doc_snippets(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for rel_path, snippets in REQUIRED_DOC_SNIPPETS.items():
        path = repo_root / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        missing.extend(f"{rel_path}:{snippet}" for snippet in snippets if snippet.lower() not in text)
    return missing


def _unsafe_public_catalog_advisor_note(repo_root: Path) -> bool:
    path = repo_root / "references" / "skill-catalog.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    start = text.find("## Advisor Note")
    if start < 0:
        return False
    end = text.find("\n## ", start + 1)
    section = text[start:end if end > 0 else None]
    lines = [line.strip() for line in section.splitlines()[2:] if line.strip()]
    if not lines:
        return False
    return lines[0] != PUBLIC_CATALOG_SAFE_ADVISOR_NOTE


def _untracked_publish_surface_files(repo_root: Path) -> list[str]:
    result = _run_git(repo_root, "ls-files", "--others", "--exclude-standard")
    if result.returncode != 0:
        return []
    hits: list[str] = []
    for raw in result.stdout.splitlines():
        path = raw.strip().replace("\\", "/")
        if not path:
            continue
        if path_excluded_from_public_export(repo_root, path):
            continue
        if path in PUBLISH_SURFACE_FILES or path.startswith(PUBLISH_SURFACE_PREFIXES):
            hits.append(path)
    return sorted(set(hits))


def _tracked_publish_surface_files(repo_root: Path) -> list[str]:
    result = _run_git(repo_root, "ls-files")
    if result.returncode != 0:
        return []
    tracked = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    tracked = [path for path in tracked if path]
    publish = []
    for path in tracked:
        if path_excluded_from_public_export(repo_root, path):
            continue
        if path in PUBLISH_SURFACE_FILES or any(path.startswith(prefix) for prefix in PUBLISH_SURFACE_PREFIXES):
            if any(path.startswith(prefix) for prefix in PUBLIC_SHAPE_SCOPE_PREFIX_BLACKLIST):
                continue
            publish.append(path)
    return sorted(set(publish))


def _publish_surface_text_candidate(rel_path: str) -> bool:
    suffix = Path(rel_path).suffix.lower()
    return suffix in {".md", ".txt", ".yaml", ".yml", ".json", ".toml"}


def _line_negates_browser_fallback(line: str) -> bool:
    lowered = line.lower()
    return bool(
        re.search(r"\b(do not|don't|avoid|never|without)\b", lowered)
        or re.search(r"\bnot\b.{0,60}\b(browser|headless)\b", lowered)
        or re.search(r"\b(browser|headless)\b.{0,60}\bnot\b", lowered)
    )


def _line_affirms_browser_fallback(line: str) -> bool:
    lowered = line.lower()
    if _line_negates_browser_fallback(line):
        return False
    return any(
        cue in lowered
        for cue in (
            "should use",
            "must use",
            "prefer ",
            "default to",
            "defaults to",
            "browser tools first",
            "headless fallback behavior",
            "browser fallback behavior",
            "headless default",
        )
    )


def _load_private_publish_guard_terms(repo_root: Path) -> list[str]:
    path = repo_root / PRIVATE_PUBLISH_GUARD_TERMS_FILE
    if not path.is_file():
        return []
    terms: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        term = raw.strip()
        if not term or term.startswith("#"):
            continue
        terms.append(term)
    return terms


def _scan_publish_surface_for_private_guard_terms(repo_root: Path) -> list[str]:
    hits: list[str] = []
    terms = _load_private_publish_guard_terms(repo_root)
    if not terms:
        return hits
    compiled = [(term, re.compile(re.escape(term), re.IGNORECASE)) for term in terms]
    for rel_path in _tracked_publish_surface_files(repo_root):
        if not _publish_surface_text_candidate(rel_path):
            continue
        path = repo_root / rel_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text:
            continue
        for line_num, line in enumerate(text.splitlines(), start=1):
            for term, pattern in compiled:
                if pattern.search(line):
                    hits.append(f"{rel_path}:{term}:{line_num}")
                    break
    return hits


def _scan_publish_surface_for_stale_continue_browser_headless(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in _tracked_publish_surface_files(repo_root):
        if not _publish_surface_text_candidate(rel_path):
            continue
        path = repo_root / rel_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_num, line in enumerate(text.splitlines(), start=1):
            if STALE_CONTINUE_BROWSER_HEADLESS_RE.search(line) and _line_affirms_browser_fallback(line):
                hits.append(f"{rel_path}:{line_num}")
    return hits


def _scan_publish_surface_for_rg_commands(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in _tracked_publish_surface_files(repo_root):
        if not rel_path.lower().endswith(".md"):
            continue
        path = repo_root / rel_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_num, line in enumerate(text.splitlines(), start=1):
            if RG_COMMAND_INVOCATION_RE.search(line):
                hits.append(f"{rel_path}:{line_num}")
    return hits


def _scan_for_no_stop_runtime_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("AGENTS.md", "INSTRUCTIONS.md", "BOUNDARIES.md", "CONTRIBUTING.md"):
        path = repo_root / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "no-stop doctrine" not in text.lower() or "minimum runtime law" not in text.lower():
            hits.append(rel_path)
    return hits


def _scan_for_debt_ledger_proof_contract(repo_root: Path) -> list[str]:
    path = repo_root / "skill_arbiter" / "collaboration_support.py"
    if not path.is_file():
        return ["skill_arbiter/collaboration_support.py"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    missing = []
    for needle in ("DEFAULT_TRUST_LEDGER", "trust_ledger", "ledger"):
        if needle not in text:
            missing.append(needle)
    return missing


def _scan_for_local_agent_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("AGENTS.md", "BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md"):
        path = repo_root / rel_path
        if not path.is_file():
            hits.append(rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "local-agent" not in text or "visible action-state parity" not in text:
            hits.append(rel_path)
    return hits


def _scan_for_reasoning_visibility_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("AGENTS.md", "BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md"):
        path = repo_root / rel_path
        if not path.is_file():
            hits.append(rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "reasoning visibility" not in text or "patience runtime window" not in text:
            hits.append(rel_path)
    return hits


def _scan_for_continue_copilot_browser_first_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("README.md", "BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md"):
        path = repo_root / rel_path
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            if re.search(r"(Continue|Copilot)[^\n\r]{0,120}(browser tools?|browser-tool|headless fallback|headless default|browser fallback)", line, re.IGNORECASE):
                if not _line_affirms_browser_fallback(line):
                    continue
                hits.append(rel_path)
                break
    return hits


def _scan_for_stale_self_diagnosis_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("README.md", "BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md"):
        path = repo_root / rel_path
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_num, line in enumerate(lines, start=1):
            if re.search(r"(Continue|Copilot)[^\n\r]{0,120}(stale session|degraded mode|waiting for a trigger|ask for a file path first)", line, re.IGNORECASE):
                hits.append(f"{rel_path}:{line_num}")
    return hits


def _scan_for_mandatory_skill_chain_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md", "AGENTS.md"):
        path = repo_root / rel_path
        if not path.is_file():
            hits.append(rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        missing = [skill for skill in MANDATORY_SKILL_CHAIN if skill not in text]
        if missing:
            hits.append(f"{rel_path}:{','.join(missing)}")
    return hits


def _scan_for_codex_parity_contract(repo_root: Path) -> list[str]:
    hits: list[str] = []
    for rel_path in ("BOUNDARIES.md", "INSTRUCTIONS.md", "CONTRIBUTING.md", "AGENTS.md"):
        path = repo_root / rel_path
        if not path.is_file():
            hits.append(rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        missing = [phrase for phrase in MANDATORY_CODEX_PARITY if phrase not in text]
        if missing:
            hits.append(f"{rel_path}:{','.join(missing)}")
    return hits


def _scan_for_codex_config_skill_bundle(repo_root: Path) -> list[str]:
    hits: list[str] = []
    required_terms = (
        "candidate-first validation",
        "trusted folders",
        "local-subagent",
        "required local-agent doctrine",
        "<codex_config_path>",
        "profiles.json",
    )
    bundle_text_parts: list[str] = []
    for rel_path in CODEX_CONFIG_SKILL_BUNDLE:
        path = repo_root / rel_path
        if not path.is_file():
            hits.append(rel_path)
            continue
        bundle_text_parts.append(path.read_text(encoding="utf-8", errors="ignore").lower())
    bundle_text = "\n".join(bundle_text_parts)
    missing = [term for term in required_terms if term not in bundle_text]
    if missing:
        hits.append(f"bundle_text:{','.join(missing)}")
    return hits


def run_public_readiness_scan(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    current_host = host_id()
    privacy = scan_repo(repo_root)
    governance = run_self_governance_scan(repo_root, privacy=privacy)
    about = about_payload(current_host)
    findings: list[dict[str, str]] = []

    for item in privacy.findings:
        detail = f"{item.path}:{item.line}:{item.col}"
        findings.append(
            _finding(
                "critical",
                f"privacy_{item.kind}",
                "privacy gate failed",
                detail,
                "remove or sanitize the tracked leak before publishing",
            )
        )

    for item in governance.get("findings", []):
        severity = str(item.get("severity") or "medium")
        findings.append(
            _finding(
                severity,
                f"self_governance_{item.get('kind', 'finding')}",
                str(item.get("detail") or "self-governance finding"),
                str(item.get("path") or ""),
                "remove or rewrite the risky runtime behavior before publishing",
            )
        )

    missing_docs = [str(path) for path in REQUIRED_DOCS if not (repo_root / path).is_file()]
    if missing_docs:
        findings.append(
            _finding(
                "high",
                "missing_required_docs",
                "required public-facing docs are missing",
                ", ".join(missing_docs),
                "restore the required policy and scope documents before publishing",
            )
        )

    readme = (repo_root / "README.md").read_text(encoding="utf-8", errors="ignore") if (repo_root / "README.md").is_file() else ""
    missing_snippets = [snippet for snippet in README_REQUIRED_SNIPPETS if snippet not in readme]
    if missing_snippets:
        findings.append(
            _finding(
                "medium",
                "readme_public_contract_incomplete",
                "README is missing public support or release-readiness guidance",
                ", ".join(missing_snippets),
                "update README support and public-release sections",
            )
        )

    missing_doc_snippets = _missing_required_doc_snippets(repo_root)
    if missing_doc_snippets:
        findings.append(
            _finding(
                "high",
                "meta_harness_doc_contract_incomplete",
                "core docs are missing required meta-harness or startup-acceptance snippets",
                ", ".join(missing_doc_snippets[:12]),
                "update the published docs so the meta-harness authority and no-empty-shell contract are explicit",
            )
        )

    missing_no_stop_runtime_contract = _scan_for_no_stop_runtime_contract(repo_root)
    if missing_no_stop_runtime_contract:
        findings.append(
            _finding(
                "high",
                "no_stop_minimum_runtime_contract_incomplete",
                "core operator docs are missing no-stop or minimum-runtime doctrine",
                ", ".join(missing_no_stop_runtime_contract),
                "restore the no-stop doctrine and minimum runtime law wording in the operator docs",
            )
        )

    missing_debt_ledger_proof_contract = _scan_for_debt_ledger_proof_contract(repo_root)
    if missing_debt_ledger_proof_contract:
        findings.append(
            _finding(
                "high",
                "debt_ledger_proof_contract_incomplete",
                "trust-ledger proof rule is missing from the collaboration support surface",
                ", ".join(missing_debt_ledger_proof_contract),
                "restore the trust-ledger proof rule and debt-ledger vocabulary in collaboration_support.py",
            )
        )

    missing_local_agent_contract = _scan_for_local_agent_contract(repo_root)
    if missing_local_agent_contract:
        findings.append(
            _finding(
                "high",
                "local_agent_contract_incomplete",
                "operator docs are missing local-agent or visible-action-state wording",
                ", ".join(missing_local_agent_contract),
                "restore the local-agent and visible action-state parity wording in the operator docs",
            )
        )

    missing_reasoning_visibility_contract = _scan_for_reasoning_visibility_contract(repo_root)
    if missing_reasoning_visibility_contract:
        findings.append(
            _finding(
                "high",
                "reasoning_visibility_contract_incomplete",
                "operator docs are missing reasoning-visibility or patience-runtime-window wording",
                ", ".join(missing_reasoning_visibility_contract),
                "restore the reasoning visibility and patience runtime window wording in the operator docs",
            )
        )

    stale_browser_first_contract = _scan_for_continue_copilot_browser_first_contract(repo_root)
    if stale_browser_first_contract:
        findings.append(
            _finding(
                "high",
                "continue_copilot_browser_first_contract",
                "Continue or Copilot lanes still advertise browser-tool-first behavior",
                ", ".join(stale_browser_first_contract),
                "rewrite Continue and Copilot lane text so browser tools are not the first-class contract",
            )
        )

    stale_self_diagnosis_contract = _scan_for_stale_self_diagnosis_contract(repo_root)
    if stale_self_diagnosis_contract:
        findings.append(
            _finding(
                "high",
                "continue_copilot_stale_self_diagnosis_contract",
                "Continue or Copilot lanes still advertise stale self-diagnosis wording",
                ", ".join(stale_self_diagnosis_contract),
                "rewrite the lane guidance so it does not tell the operator to wait, downgrade, or ask for a path first",
            )
        )

    mandatory_skill_chain_contract = _scan_for_mandatory_skill_chain_contract(repo_root)
    if mandatory_skill_chain_contract:
        findings.append(
            _finding(
                "high",
                "mandatory_skill_chain_contract_incomplete",
                "operator docs are missing one or more mandatory skill-arbiter chain references",
                ", ".join(mandatory_skill_chain_contract),
                "restore the mandatory local-agent skill chain language across operator docs and guidance",
            )
        )

    codex_parity_contract = _scan_for_codex_parity_contract(repo_root)
    if codex_parity_contract:
        findings.append(
            _finding(
                "high",
                "codex_parity_contract_incomplete",
                "operator docs are missing Codex config parity wording for local-agent workflows",
                ", ".join(codex_parity_contract),
                "restore trusted folders, local-subagent state, reasoning visibility, and local-agent doctrine wording in the operator docs",
            )
        )

    codex_skill_bundle_contract = _scan_for_codex_config_skill_bundle(repo_root)
    if codex_skill_bundle_contract:
        findings.append(
            _finding(
                "high",
                "codex_config_skill_bundle_incomplete",
                "codex-config-self-maintenance skill bundle is missing required contract or evidence text",
                ", ".join(codex_skill_bundle_contract),
                "restore candidate-first validation, trusted folders, local-subagent state, and config-path evidence in the skill bundle",
            )
        )

    missing_icons = [str(path) for path in REQUIRED_ICON_ASSETS if not (repo_root / path).is_file()]
    if missing_icons:
        findings.append(
            _finding(
                "high",
                "missing_icon_assets",
                "desktop icon assets are missing",
                ", ".join(missing_icons),
                "restore the published PNG and ICO assets before packaging or releasing",
            )
        )

    missing_launch_surfaces = [str(path) for path in REQUIRED_LAUNCH_SURFACES if not (repo_root / path).is_file()]
    if missing_launch_surfaces:
        findings.append(
            _finding(
                "high",
                "missing_no_shell_launcher",
                "required shell-free desktop launch surface is missing",
                ", ".join(missing_launch_surfaces),
                "restore the no-shell VBS launcher before publishing",
            )
        )

    launch_docs = {
        rel: (repo_root / rel).read_text(encoding="utf-8", errors="ignore")
        for rel in ("README.md", "CONTRIBUTING.md", "SKILL.md")
        if (repo_root / rel).is_file()
    }
    shell_wrapped_docs = [rel for rel, text in launch_docs.items() if SHELL_WRAPPED_DESKTOP_LAUNCH_RE.search(text)]
    if shell_wrapped_docs:
        findings.append(
            _finding(
                "high",
                "shell_wrapped_desktop_launch_docs",
                "repo docs still advertise a shell-wrapped desktop launch path",
                ", ".join(shell_wrapped_docs),
                "switch public launch guidance to shell-free launcher surfaces and demote shell wrappers to developer-helper status",
            )
        )

    runtime_rel = "apps/nullclaw-desktop/runtime"
    if _git_file_tracked(repo_root, runtime_rel):
        findings.append(
            _finding(
                "critical",
                "tracked_runtime_dir",
                "runtime output directory is tracked by git",
                runtime_rel,
                "remove tracked runtime artifacts and keep the path ignored",
            )
        )
    elif not _git_file_ignored(repo_root, runtime_rel):
        findings.append(
            _finding(
                "high",
                "runtime_dir_not_ignored",
                "runtime output directory is not ignored",
                runtime_rel,
                "ignore the runtime directory before publishing",
            )
        )

    codex_index_rel = ".codex-index"
    if _git_file_tracked(repo_root, codex_index_rel):
        findings.append(
            _finding(
                "high",
                "tracked_codex_index",
                "bounded local index output is tracked by git",
                codex_index_rel,
                "remove tracked local index artifacts and keep the path ignored",
            )
        )
    elif not _git_file_ignored(repo_root, codex_index_rel):
        findings.append(
            _finding(
                "medium",
                "codex_index_not_ignored",
                "bounded local index output is not ignored",
                codex_index_rel,
                "ignore local index artifacts before publish-prep workflows create dirty state",
            )
        )

    tracked_suspicious = _tracked_pattern_matches(repo_root)
    tracked_suspicious = [item for item in tracked_suspicious if not item.startswith("apps/nullclaw-desktop/assets/")]
    if tracked_suspicious:
        findings.append(
            _finding(
                "high",
                "suspicious_tracked_artifacts",
                "tracked repo files look like local evidence or shortcut/runtime artifacts",
                ", ".join(tracked_suspicious[:12]),
                "move host-local evidence to ignored storage before publishing",
            )
        )

    unsanitized_host_ids = _unsanitized_host_id_hits(repo_root)
    if unsanitized_host_ids:
        findings.append(
            _finding(
                "critical",
                "unsanitized_host_id",
                "repo-tracked artifacts contain a real host identifier",
                ", ".join(unsanitized_host_ids[:12]),
                "replace host identifiers with <LOCAL_HOST_ID> before publishing",
            )
        )

    shortcut_script = repo_root / "scripts" / "install_security_console_shortcut.ps1"
    if not shortcut_script.is_file():
        findings.append(
            _finding(
                "medium",
                "missing_shortcut_installer",
                "desktop shortcut installer is missing",
                str(shortcut_script.relative_to(repo_root)),
                "add the launch-surface installer so the app ships with a branded desktop entry",
            )
        )

    malformed_support = [
        f"{item['label']}={item['value']}"
        for item in about.get("support_channels", [])
        if not str(item.get("value") or "").startswith("https://")
    ]
    if malformed_support:
        findings.append(
            _finding(
                "high",
                "invalid_support_urls",
                "support metadata includes non-HTTPS or malformed public URLs",
                ", ".join(malformed_support),
                "fix public support metadata before publishing",
            )
        )

    if _unsafe_public_catalog_advisor_note(repo_root):
        findings.append(
            _finding(
                "medium",
                "unsafe_public_catalog_advisor_note",
                "public catalog includes ephemeral live advisor prose",
                "references/skill-catalog.md",
                "replace the catalog advisor note with a stable public-shape placeholder",
            )
        )

    untracked_publish_surface = _untracked_publish_surface_files(repo_root)
    if untracked_publish_surface:
        findings.append(
            _finding(
                "high",
                "untracked_publish_surface",
                "publish-surface files are still untracked in git",
                ", ".join(untracked_publish_surface[:12]),
                "track or remove untracked source/docs files before publishing so clean checkouts match the audited repo state",
            )
        )

    stale_browser_headless_hits = _scan_publish_surface_for_stale_continue_browser_headless(repo_root)
    if stale_browser_headless_hits:
        findings.append(
            _finding(
                "high",
                "stale_continue_browser_headless",
                "public-shape artifacts still advertise Continue browser/headless fallback wording",
                ", ".join(stale_browser_headless_hits[:12]),
                "remove stale Continue browser-tool or headless-fallback wording from publishable docs and code",
            )
        )

    rg_command_hits = _scan_publish_surface_for_rg_commands(repo_root)
    if rg_command_hits:
        findings.append(
            _finding(
                "high",
                "ripgrep_publish_guidance",
                "publish-surface artifacts still instruct using rg or rg.exe",
                ", ".join(rg_command_hits[:12]),
                "replace ripgrep command examples with PowerShell Select-String or Get-ChildItem guidance before publishing",
            )
        )

    private_guard_term_hits = _scan_publish_surface_for_private_guard_terms(repo_root)
    if private_guard_term_hits:
        findings.append(
            _finding(
                "critical",
                "public_shape_private_guard_term",
                "public-shape artifacts contain sealed private-vocabulary terms",
                ", ".join(private_guard_term_hits[:12]),
                "move the sealed private vocabulary back into private-only surfaces before publishing",
            )
        )

    candidate_meta_harness = scan_candidate_meta_harness(repo_root / "skill-candidates")
    for item in candidate_meta_harness:
        findings.append(
            _finding(
                item.severity,
                f"candidate_{item.code}",
                item.message,
                item.path,
                "update the candidate skill so it follows the meta-harness root and authority contract before publishing",
            )
        )

    counts = {
        "critical_count": sum(1 for item in findings if item["severity"] == "critical"),
        "high_count": sum(1 for item in findings if item["severity"] == "high"),
        "medium_count": sum(1 for item in findings if item["severity"] == "medium"),
    }
    payload = {
        "host_id": current_host,
        "passed": counts["critical_count"] == 0 and counts["high_count"] == 0,
        **counts,
        "checks": {
            "privacy_gate": privacy.passed,
            "self_governance": bool(governance.get("passed")),
            "required_docs": not missing_docs,
            "meta_harness_docs": not missing_doc_snippets,
            "support_metadata": not malformed_support,
            "icon_assets": not missing_icons,
            "launch_surfaces": not missing_launch_surfaces,
            "startup_acceptance_docs": not shell_wrapped_docs,
            "runtime_gitignore": _git_file_ignored(repo_root, runtime_rel) and not _git_file_tracked(repo_root, runtime_rel),
            "codex_index_gitignore": _git_file_ignored(repo_root, codex_index_rel) and not _git_file_tracked(repo_root, codex_index_rel),
            "shortcut_installer": shortcut_script.is_file(),
            "public_catalog_advisor_note": not _unsafe_public_catalog_advisor_note(repo_root),
            "tracked_publish_surface": not untracked_publish_surface,
            "candidate_meta_harness": not candidate_meta_harness,
        },
        "findings": findings,
    }
    if repo_root == REPO_ROOT:
        public_readiness_cache_path().write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    return payload


def load_cached_public_readiness() -> dict[str, object]:
    path = public_readiness_cache_path()
    if not path.is_file():
        return run_public_readiness_scan()
    return json.loads(path.read_text(encoding="utf-8"))
