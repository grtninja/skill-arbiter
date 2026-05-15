from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from skill_arbiter import quarantine
from skill_arbiter.agent_http import _origin_allowed, _resolve_allowed_origin, _write_cors_headers


REPO_ROOT = Path(__file__).resolve().parents[1]


class _HeaderProbe:
    def __init__(self, origin: str = "") -> None:
        self.headers = {"Origin": origin} if origin else {}
        self.sent: list[tuple[str, str]] = []

    def send_header(self, key: str, value: str) -> None:
        self.sent.append((key, value))


def _patch_quarantine_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(quarantine, "quarantine_state_path", lambda: tmp_path / "quarantine-state.json")
    monkeypatch.setattr(quarantine, "quarantine_artifacts_root", lambda: tmp_path / "quarantine")
    monkeypatch.setattr(quarantine, "append_audit_event", lambda event: None)
    monkeypatch.setattr(quarantine, "host_id", lambda: "test-host")


def test_cors_rejects_null_origin_and_avoids_wildcard() -> None:
    assert _resolve_allowed_origin("null") == ""
    assert _origin_allowed(_HeaderProbe()) is True
    assert _origin_allowed(_HeaderProbe("null")) is False
    assert _origin_allowed(_HeaderProbe("https://example.com")) is False

    no_origin = _HeaderProbe()
    _write_cors_headers(no_origin)
    assert ("Access-Control-Allow-Origin", "*") not in no_origin.sent
    assert not any(key == "Access-Control-Allow-Origin" for key, _value in no_origin.sent)
    assert not any(key == "Access-Control-Allow-Private-Network" for key, _value in no_origin.sent)

    loopback = _HeaderProbe("http://127.0.0.1:3000")
    _write_cors_headers(loopback)
    assert ("Access-Control-Allow-Origin", "http://127.0.0.1:3000") in loopback.sent
    assert ("Access-Control-Allow-Private-Network", "true") in loopback.sent


def test_quarantine_rejects_traversal_skill_names(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_quarantine_state(monkeypatch, tmp_path)
    skills_root = tmp_path / "skills"
    victim = tmp_path / "victim"
    victim.mkdir()

    for unsafe_name in ["../victim", "..\\victim", "/tmp/victim", "safe/../victim", ""]:
        with pytest.raises(ValueError):
            quarantine.apply_quarantine(unsafe_name, skills_root)
        with pytest.raises(ValueError):
            quarantine.release_quarantine(unsafe_name, skills_root)
        with pytest.raises(ValueError):
            quarantine.confirm_delete_skill(unsafe_name, skills_root)

    assert victim.exists()


def test_delete_rejects_symlinked_skill_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_quarantine_state(monkeypatch, tmp_path)
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "payload.txt").write_text("keep me\n", encoding="utf-8")
    link = skills_root / "linked-skill"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - Windows developer hosts may require symlink privilege.
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(ValueError):
        quarantine.confirm_delete_skill("linked-skill", skills_root)

    assert (outside / "payload.txt").is_file()


def test_cross_repo_radar_disables_hook_and_filter_configs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script = REPO_ROOT / "skill-candidates" / "skills-cross-repo-radar" / "scripts" / "repo_change_radar.py"
    spec = importlib.util.spec_from_file_location("repo_change_radar", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(cmd, 0, "ok\n", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    rc, output = module._run_git(tmp_path, ["status", "--porcelain"])

    assert rc == 0
    assert output == "ok"
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[:3] == ["git", "-C", str(tmp_path)]
    assert "status" in cmd
    for safe_config in module.SAFE_GIT_CONFIG:
        config_index = cmd.index(safe_config)
        assert cmd[config_index - 1] == "-c"
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
