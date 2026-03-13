from __future__ import annotations

import json

from .contracts import AuditEvent
from .paths import audit_log_path


def append_audit_event(event: AuditEvent) -> None:
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_dict(), ensure_ascii=True) + "\n")


def read_audit_events(limit: int = 200) -> list[dict[str, object]]:
    path = audit_log_path()
    if not path.is_file():
        return []
    rows = path.read_text(encoding="utf-8").splitlines()
    payload = [json.loads(line) for line in rows[-limit:] if line.strip()]
    return list(reversed(payload))
