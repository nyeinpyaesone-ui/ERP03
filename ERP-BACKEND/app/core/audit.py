from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    actor_id: int | None
    actor_kind: str
    domain: str
    action: str
    resource_id: str | None
    payload: dict[str, Any]
    at: datetime


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        *,
        actor_id: int | None,
        actor_kind: str,
        domain: str,
        action: str,
        resource_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,
            actor_kind=actor_kind,
            domain=domain,
            action=action,
            resource_id=resource_id,
            payload=payload or {},
            at=datetime.now(timezone.utc),
        )
        self._events.append(event)
        return event

    def recent(self, limit: int = 100) -> list[AuditEvent]:
        return self._events[-limit:]


audit_log = AuditLog()
