"""Optimized database session with connection pooling and auto-tuning."""

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.metrics import DB_POOL_ACTIVE, DB_POOL_IDLE


def _create_engine() -> Any:
    """Build the async engine with dialect-appropriate pooling.

    Production (PostgreSQL): size-based pooling with pre-ping, recycle,
    prepared-statement caching, and bounded checkout waits.

    Development (SQLite): no size-based pooling (unsupported by aiosqlite).
    Pool settings auto-tuned from environment or sensible defaults.
    """
    connect_args: dict[str, Any] = {}
    if not settings.database_url.startswith("sqlite"):
        # Prepared-statement threshold reduces parse overhead on repeated queries.
        connect_args["prepare_threshold"] = None  # type: ignore[dict-item]
        kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "echo": settings.db_echo,
            "future": True,
            "connect_args": connect_args,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        }
        # Wire pool metrics to SQLAlchemy pool events.
        engine = create_async_engine(settings.database_url, **kwargs)
        _wire_pool_metrics(engine.pool)
        return engine
    kwargs = {
        "pool_pre_ping": True,
        "echo": settings.db_echo,
        "future": True,
    }
    return create_async_engine(settings.database_url, **kwargs)


def _wire_pool_metrics(pool: Any) -> None:
    """Attach Prometheus gauges to SQLAlchemy pool lifecycle events."""

    @event.listens_for(pool, "connect")
    def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:
        DB_POOL_ACTIVE.inc()

    @event.listens_for(pool, "checkout")
    def _on_checkout(dbapi_connection: Any, connection_record: Any) -> None:
        DB_POOL_ACTIVE.inc()
        DB_POOL_IDLE.dec()

    @event.listens_for(pool, "checkin")
    def _on_checkin(dbapi_connection: Any, connection_record: Any) -> None:
        DB_POOL_IDLE.inc()

    @event.listens_for(pool, "close")
    def _on_close(dbapi_connection: Any, connection_record: Any) -> None:
        DB_POOL_ACTIVE.dec()


engine = _create_engine()

SessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
