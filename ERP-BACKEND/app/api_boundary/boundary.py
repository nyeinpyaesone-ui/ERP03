from __future__ import annotations

from typing import Any, Callable

from app.core.audit import audit_log


class BoundaryError(Exception):
    pass


class PermissionDenied(Exception):
    pass


def has_permission(actor, resource: str, action: str, db) -> bool:
    """Simplified permission check for actors."""
    if getattr(actor, 'actor_kind', None) == 'ai_agent':
        return action == 'read'
    return True


class ERPBoundary:
    def __init__(self) -> None:
        self._queries: dict[str, Callable[..., Any]] = {}
        self._commands: dict[str, Callable[..., Any]] = {}

    def register_query(self, name: str, fn: Callable[..., Any]) -> None:
        self._queries[name] = fn

    def register_command(self, name: str, fn: Callable[..., Any]) -> None:
        self._commands[name] = fn

    def query(self, *, name: str, actor, db, params: dict | None = None) -> Any:
        if name not in self._queries:
            raise BoundaryError(f"Unknown query '{name}'")
        domain, action = name.split(".", 1)
        self._authorize(actor, domain, action="read", db=db)
        result = self._queries[name](db=db, **(params or {}))
        audit_log.record(
            actor_id=getattr(actor, "id", None),
            actor_kind=self._actor_kind(actor),
            domain=domain,
            action=f"query.{action}",
            payload={"params": params or {}},
        )
        return result

    def command(self, *, name: str, actor, db, params: dict | None = None) -> Any:
        if name not in self._commands:
            raise BoundaryError(f"Unknown command '{name}'")
        domain, action = name.split(".", 1)
        self._authorize(actor, domain, action="write", db=db)
        result = self._commands[name](db=db, actor=actor, **(params or {}))
        audit_log.record(
            actor_id=getattr(actor, "id", None),
            actor_kind=self._actor_kind(actor),
            domain=domain,
            action=f"command.{action}",
            payload={"params": params or {}},
        )
        return result

    def _authorize(self, actor, domain: str, action: str, db) -> None:
        if actor is None:
            raise BoundaryError("Unauthenticated actor cannot cross the ERP API boundary")
        if self._actor_kind(actor) == "ai_agent":
            if action == "write" and domain not in AI_WRITE_ALLOWLIST:
                raise BoundaryError(f"AI agents may not write to domain '{domain}'")

    @staticmethod
    def _actor_kind(actor) -> str:
        return getattr(actor, "actor_kind", "user")


AI_WRITE_ALLOWLIST: set[str] = set()

boundary = ERPBoundary()

# Register finance domain queries
from app.domains.finance.application import dashboard as finance_dashboard
boundary.register_query("finance.dashboard", finance_dashboard)
