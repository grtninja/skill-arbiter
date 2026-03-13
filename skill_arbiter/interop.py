from __future__ import annotations

from pathlib import Path

from .contracts import SourceRecord
from .paths import REPO_ROOT, host_id


PATTERN_MAP = {
    "codex-app": ("AGENTS.md", "docs/AGENTS.md"),
    "vscode-codex": (".vscode/**/*.instructions.md", ".vscode/settings.json", ".vscode/mcp.json", ".vscode/*.code-workspace"),
    "github-copilot": (".github/copilot-instructions.md", ".github/instructions/**/*.instructions.md", ".github/prompts/**/*.prompt.md"),
}
DOC_URLS = {
    "codex-local": "https://platform.openai.com/docs/codex/overview",
    "codex-app": "https://platform.openai.com/docs/codex/overview",
    "vscode-codex": "https://code.visualstudio.com/docs/copilot/customization/custom-instructions",
    "github-copilot": "https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot",
}


def _workspace_root() -> Path:
    return REPO_ROOT.parent


def _repo_roots(workspace_root: Path) -> list[Path]:
    rows: list[Path] = []
    if not workspace_root.is_dir():
        return rows
    for child in sorted(workspace_root.iterdir(), key=lambda item: item.name.lower()):
        if child.is_dir() and (child / ".git").exists():
            rows.append(child)
    return rows


def _local_codex_rows(current_host: str) -> list[SourceRecord]:
    codex_root = Path.home() / ".codex"
    config_path = codex_root / "config.toml"
    skills_root = codex_root / "skills"
    notes = []
    if config_path.is_file():
        notes.append("config=present")
    if skills_root.is_dir():
        try:
            skill_count = sum(1 for item in skills_root.iterdir() if item.is_dir())
        except OSError:
            skill_count = 0
        notes.append(f"skills={skill_count}")
    return [
        SourceRecord(
            source_id="codex-local",
            source_type="interop_surface",
            origin="local Codex config",
            version_or_commit="local-scan",
            local_presence="present" if config_path.is_file() or skills_root.is_dir() else "not_detected",
            drift_state="tracked",
            risk_class="monitor",
            recommended_action="keep_in_sync",
            host_id=current_host,
            remote_url=DOC_URLS["codex-local"],
            compatibility_surface="local",
            notes=notes,
        )
    ]


def scan_interop_sources(workspace_root: Path | None = None) -> list[SourceRecord]:
    root = workspace_root or _workspace_root()
    repos = _repo_roots(root)
    current_host = host_id()
    rows: list[SourceRecord] = _local_codex_rows(current_host)
    for source_id, patterns in PATTERN_MAP.items():
        match_count = 0
        repo_count = 0
        for repo in repos:
            repo_matches = 0
            for pattern in patterns:
                repo_matches += len(list(repo.glob(pattern)))
            if repo_matches:
                match_count += repo_matches
                repo_count += 1
        rows.append(
            SourceRecord(
                source_id=source_id,
                source_type="interop_surface",
                origin="workspace instruction surface",
                version_or_commit="local-scan",
                local_presence="present" if match_count else "not_detected",
                drift_state="tracked",
                risk_class="monitor",
                recommended_action="keep_in_sync",
                host_id=current_host,
                remote_url=DOC_URLS.get(source_id, ""),
                compatibility_surface="workspace",
                notes=[f"repos={repo_count}", f"files={match_count}"],
            )
        )
    return rows
