from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .about import about_payload
from .meta_harness_policy import scan_candidate_meta_harness
from .paths import REPO_ROOT, host_id, public_readiness_cache_path, windows_no_window_subprocess_kwargs
from .privacy_policy import scan_repo
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
        "http://127.0.0.1:2337/v1",
        "LM Studio",
        "operator surface",
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
    ],
    Path("README.md"): [
        "http://127.0.0.1:2337/v1",
        "LM Studio",
        "operator surface",
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
    ],
}
README_REQUIRED_SNIPPETS = [
    "## Public support",
    "## Public release readiness",
    "## Safety and abuse handling",
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
        text = path.read_text(encoding="utf-8", errors="ignore")
        missing.extend(f"{rel_path}:{snippet}" for snippet in snippets if snippet not in text)
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
        if path in PUBLISH_SURFACE_FILES or path.startswith(PUBLISH_SURFACE_PREFIXES):
            hits.append(path)
    return sorted(set(hits))


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
