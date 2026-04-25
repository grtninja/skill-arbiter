from __future__ import annotations

import os
import sqlite3
import subprocess
import time
from pathlib import Path
from shutil import which
from typing import Any, Iterable

from .paths import ensure_state_dirs, windows_no_window_subprocess_kwargs


SCHEMA_VERSION = 1
DEFAULT_PROCESS_LIMITS = {
    "rg": {
        "max_instances": 1,
        "max_age_seconds": 45,
        "action": "kill_excess",
        "reason": "allow one bounded ripgrep instance; kill agent-spawned churn above the limit",
    },
    "rg.exe": {
        "max_instances": 1,
        "max_age_seconds": 45,
        "action": "kill_excess",
        "reason": "allow one bounded ripgrep instance; kill agent-spawned churn above the limit",
    },
}


class ProcessPolicyError(RuntimeError):
    """Raised when a command violates the local process policy database."""


def process_policy_db_path() -> Path:
    return ensure_state_dirs() / "process-policy.sqlite3"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _normalize_executable(value: str | os.PathLike[str]) -> str:
    raw = str(value or "").strip().strip('"').strip("'")
    if not raw:
        return ""
    return Path(raw).name.lower()


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or process_policy_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _table_sql(connection: sqlite3.Connection, table: str) -> str:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return str(row["sql"] if row is not None else "")


def _migrate_legacy_policy_table(connection: sqlite3.Connection) -> None:
    sql = _table_sql(connection, "executable_policy")
    if not sql:
        return
    if "kill_excess" in sql and "max_instances" in sql and "max_age_seconds" in sql:
        return
    legacy_name = f"executable_policy_legacy_{_now_ms()}"
    connection.execute(f"ALTER TABLE executable_policy RENAME TO {legacy_name}")
    connection.execute(
        """
        INSERT INTO process_policy_audit(event_type, executable, command, pid, reason, created_at_ms)
        VALUES('schema_migrated', 'executable_policy', ?, NULL, 'upgraded process policy table for bounded instance limits', ?)
        """,
        (legacy_name, _now_ms()),
    )


def initialize(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS process_policy_audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_type TEXT NOT NULL,
          executable TEXT NOT NULL,
          command TEXT NOT NULL DEFAULT '',
          pid INTEGER,
          reason TEXT NOT NULL DEFAULT '',
          created_at_ms INTEGER NOT NULL
        )
        """
    )
    _migrate_legacy_policy_table(connection)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS executable_policy (
          executable TEXT PRIMARY KEY,
          action TEXT NOT NULL CHECK (action IN ('allow', 'deny', 'deny_and_kill', 'kill_excess')),
          enabled INTEGER NOT NULL DEFAULT 1,
          max_instances INTEGER NOT NULL DEFAULT 1,
          max_age_seconds INTEGER NOT NULL DEFAULT 45,
          reason TEXT NOT NULL DEFAULT '',
          source TEXT NOT NULL DEFAULT 'local',
          created_at_ms INTEGER NOT NULL,
          updated_at_ms INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS process_policy_audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_type TEXT NOT NULL,
          executable TEXT NOT NULL,
          command TEXT NOT NULL DEFAULT '',
          pid INTEGER,
          reason TEXT NOT NULL DEFAULT '',
          created_at_ms INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_process_policy_audit_created
          ON process_policy_audit(created_at_ms);
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    now = _now_ms()
    for executable, policy in DEFAULT_PROCESS_LIMITS.items():
        connection.execute(
            """
            INSERT INTO executable_policy(
              executable, action, enabled, max_instances, max_age_seconds, reason, source, created_at_ms, updated_at_ms
            )
            VALUES(?, ?, 1, ?, ?, ?, 'default', ?, ?)
            ON CONFLICT(executable) DO UPDATE SET
              action=excluded.action,
              enabled=excluded.enabled,
              max_instances=excluded.max_instances,
              max_age_seconds=excluded.max_age_seconds,
              reason=excluded.reason,
              source=excluded.source,
              updated_at_ms=excluded.updated_at_ms
            """,
            (
                _normalize_executable(executable),
                str(policy["action"]),
                int(policy["max_instances"]),
                int(policy["max_age_seconds"]),
                str(policy["reason"]),
                now,
                now,
            ),
        )
    connection.commit()


def ensure_initialized(path: Path | None = None) -> Path:
    db_path = path or process_policy_db_path()
    with connect(db_path) as connection:
        initialize(connection)
    return db_path


def set_executable_limit(
    executable: str,
    *,
    action: str = "kill_excess",
    max_instances: int = 1,
    max_age_seconds: int = 45,
    reason: str = "",
    source: str = "operator",
    path: Path | None = None,
) -> dict[str, Any]:
    normalized = _normalize_executable(executable)
    if not normalized:
        raise ValueError("executable is required")
    if action not in {"allow", "deny", "deny_and_kill", "kill_excess"}:
        raise ValueError("unsupported process policy action")
    if max_instances < 0:
        raise ValueError("max_instances must be >= 0")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be >= 0")
    now = _now_ms()
    with connect(path) as connection:
        initialize(connection)
        connection.execute(
            """
            INSERT INTO executable_policy(
              executable, action, enabled, max_instances, max_age_seconds, reason, source, created_at_ms, updated_at_ms
            )
            VALUES(?, ?, 1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(executable) DO UPDATE SET
              action=excluded.action,
              enabled=1,
              max_instances=excluded.max_instances,
              max_age_seconds=excluded.max_age_seconds,
              reason=excluded.reason,
              source=excluded.source,
              updated_at_ms=excluded.updated_at_ms
            """,
            (normalized, action, max_instances, max_age_seconds, reason, source, now, now),
        )
        _record_audit(
            connection,
            event_type="policy_updated",
            executable=normalized,
            command="",
            pid=None,
            reason=reason,
        )
        connection.commit()
    return {
        "executable": normalized,
        "action": action,
        "enabled": True,
        "max_instances": max_instances,
        "max_age_seconds": max_age_seconds,
        "reason": reason,
        "source": source,
    }


def deny_executable(
    executable: str,
    *,
    action: str = "deny_and_kill",
    reason: str = "",
    source: str = "operator",
    path: Path | None = None,
) -> dict[str, Any]:
    return set_executable_limit(
        executable,
        action=action,
        max_instances=0,
        max_age_seconds=0,
        reason=reason,
        source=source,
        path=path,
    )


def denied_policy_for(executable: str, *, path: Path | None = None) -> dict[str, Any] | None:
    normalized = _normalize_executable(executable)
    if not normalized:
        return None
    with connect(path) as connection:
        initialize(connection)
        row = connection.execute(
            """
            SELECT executable, action, enabled, max_instances, max_age_seconds, reason, source, created_at_ms, updated_at_ms
            FROM executable_policy
            WHERE executable = ? AND enabled = 1 AND action IN ('deny', 'deny_and_kill')
            """,
            (normalized,),
        ).fetchone()
    return dict(row) if row is not None else None


def executable_policies(*, path: Path | None = None) -> list[dict[str, Any]]:
    with connect(path) as connection:
        initialize(connection)
        sql = """
            SELECT executable, action, enabled, max_instances, max_age_seconds, reason, source, created_at_ms, updated_at_ms
            FROM executable_policy
            WHERE enabled = 1
            ORDER BY executable
        """
        return [dict(row) for row in connection.execute(sql).fetchall()]


def denied_policies(*, kill_only: bool = False, path: Path | None = None) -> list[dict[str, Any]]:
    rows = [row for row in executable_policies(path=path) if row.get("action") in {"deny", "deny_and_kill"}]
    if kill_only:
        rows = [row for row in rows if row.get("action") == "deny_and_kill"]
    return rows


def _record_audit(
    connection: sqlite3.Connection,
    *,
    event_type: str,
    executable: str,
    command: str,
    pid: int | None,
    reason: str,
) -> None:
    connection.execute(
        """
        INSERT INTO process_policy_audit(event_type, executable, command, pid, reason, created_at_ms)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (event_type, executable, command, pid, reason, _now_ms()),
    )


def enforce_subprocess_policy(cmd: Iterable[str | os.PathLike[str]], *, path: Path | None = None) -> None:
    parts = [str(part) for part in cmd]
    executable = _normalize_executable(parts[0] if parts else "")
    policy = denied_policy_for(executable, path=path)
    if policy is None:
        return
    command = " ".join(parts)
    with connect(path) as connection:
        initialize(connection)
        _record_audit(
            connection,
            event_type="subprocess_blocked",
            executable=executable,
            command=command,
            pid=None,
            reason=str(policy.get("reason") or ""),
        )
        connection.commit()
    raise ProcessPolicyError(f"blocked executable by Skill Arbiter process policy DB: {executable}")


def _powershell_process_rows(executable: str) -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    stem = Path(executable).stem
    completed = subprocess.run(
        [
            which("powershell.exe") or "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-Command",
            (
                f"$now=Get-Date; Get-Process -Name {stem!r} -ErrorAction SilentlyContinue | "
                "Select-Object Id,ProcessName,Path,StartTime,@{Name='AgeSeconds';Expression={[int](($now - $_.StartTime).TotalSeconds)}} | "
                "ConvertTo-Json -Depth 4"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
        **windows_no_window_subprocess_kwargs(),
    )
    raw = completed.stdout.strip()
    if not raw:
        return []
    try:
        payload = __import__("json").loads(raw)
    except Exception:
        return []
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _powershell_process_count(executable: str) -> int:
    return len(_powershell_process_rows(executable))


def count_denied_processes(*, path: Path | None = None) -> dict[str, int]:
    return {row["executable"]: _powershell_process_count(str(row["executable"])) for row in executable_policies(path=path)}


def enforce_denied_processes(*, dry_run: bool = False, path: Path | None = None) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    remaining: dict[str, int] = {}
    if os.name != "nt":
        return {"available": False, "dry_run": dry_run, "actions": actions, "remaining": remaining}

    with connect(path) as connection:
        initialize(connection)
        for policy in executable_policies(path=path):
            executable = str(policy["executable"])
            action = str(policy["action"])
            rows = _powershell_process_rows(executable)
            max_instances = int(policy.get("max_instances") or 0)
            max_age_seconds = int(policy.get("max_age_seconds") or 0)
            kill_rows: list[dict[str, Any]] = []
            if action in {"deny_and_kill", "deny"}:
                kill_rows = rows
            elif action == "kill_excess":
                sorted_rows = sorted(rows, key=lambda row: int(row.get("AgeSeconds") or 0), reverse=True)
                old_rows = [row for row in sorted_rows if max_age_seconds > 0 and int(row.get("AgeSeconds") or 0) > max_age_seconds]
                excess_rows = sorted_rows[max_instances:] if len(sorted_rows) > max_instances else []
                by_pid: dict[int, dict[str, Any]] = {}
                for row in old_rows + excess_rows:
                    try:
                        by_pid[int(row.get("Id") or 0)] = row
                    except Exception:
                        continue
                kill_rows = list(by_pid.values())
            if kill_rows and not dry_run:
                pid_list = ",".join(str(int(row.get("Id") or 0)) for row in kill_rows if int(row.get("Id") or 0) > 0)
                if pid_list:
                    subprocess.run(
                        [
                            which("powershell.exe") or "powershell.exe",
                            "-NoLogo",
                            "-NoProfile",
                            "-NonInteractive",
                            "-WindowStyle",
                            "Hidden",
                            "-Command",
                            f"$ErrorActionPreference='SilentlyContinue'; '{pid_list}' -split ',' | ForEach-Object {{ Stop-Process -Id ([int]$_) -Force }}",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        **windows_no_window_subprocess_kwargs(),
                    )
                _record_audit(
                    connection,
                    event_type="process_limit_enforced",
                    executable=executable,
                    command=str(kill_rows)[:2000],
                    pid=None,
                    reason=str(policy.get("reason") or ""),
                )
            if kill_rows:
                actions.append(
                    [
                        {
                            "executable": executable,
                            "action": action,
                            "observed_count": len(rows),
                            "kill_count": len(kill_rows),
                            "dry_run": dry_run,
                            "max_instances": max_instances,
                            "max_age_seconds": max_age_seconds,
                        }
                    ][0]
                )
            remaining[executable] = _powershell_process_count(executable)
        connection.commit()
    return {"available": True, "dry_run": dry_run, "actions": actions, "remaining": remaining}


def status(*, path: Path | None = None) -> dict[str, Any]:
    db_path = ensure_initialized(path)
    policies = executable_policies(path=db_path)
    counts = count_denied_processes(path=db_path)
    with connect(db_path) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        recent_audit = [
            dict(row)
            for row in connection.execute(
                """
                SELECT event_type, executable, command, pid, reason, created_at_ms
                FROM process_policy_audit
                ORDER BY created_at_ms DESC, id DESC
                LIMIT 20
                """
            ).fetchall()
        ]
    return {
        "database": str(db_path),
        "integrity": integrity,
        "policies": policies,
        "denied_process_counts": counts,
        "recent_audit": recent_audit,
    }
