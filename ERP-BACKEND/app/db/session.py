"""Optimized database session with connection pooling and auto-tuning."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def _create_engine() -> create_async_engine:
    """Build the async engine with dialect-appropriate pooling.

    Production (PostgreSQL): size-based pooling with pre-ping and recycle.
    Development (SQLite): no size-based pooling (unsupported by aiosqlite).
    Pool settings auto-tuned from environment or sensible defaults.
    """
    kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "echo": settings.db_echo,
        "future": True,
    }
    if not settings.database_url.startswith("sqlite"):
        kwargs.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_recycle=settings.db_pool_recycle,
        )
    return create_async_engine(settings.database_url, **kwargs)


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
