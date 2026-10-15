from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

def _create_engine():
    """Build the async engine with driver-appropriate pooling.

    SQLite (aiosqlite) does not support size-based pooling; applying pool
    kwargs there raises at first connect. Detect the dialect and configure
    accordingly so one codebase runs on both development (SQLite) and
    production (PostgreSQL/asyncpg) backends.
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
