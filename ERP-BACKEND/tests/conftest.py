"""Shared pytest configuration for the backend test suite.

The service is PostgreSQL-only (UUID columns, advisory locks, row-level
FOR UPDATE). Integration tests therefore require a reachable database via
DATABASE_URL; they are skipped automatically when none is available so unit
suites stay runnable anywhere.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

os.environ.setdefault("DATABASE_PATH", "/tmp/erp03-tests.sqlite3")

_INTEGRATION_MARKERS = ("integration", "requires_database")


def pytest_configure(config):
    for marker in _INTEGRATION_MARKERS:
        config.addinivalue_line(
            "markers", f"{marker}: requires a reachable PostgreSQL DATABASE_URL"
        )


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


async def _database_available() -> bool:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://erp03:erp03@postgres:5432/erp03",
    )
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(session, config, items):
    postgres_ready = _database_available_cached()
    skip_postgres = pytest.mark.skip(
        reason="PostgreSQL test database unavailable (set DATABASE_URL)"
    )
    for item in items:
        if item.get_closest_marker("integration"):
            # PostgreSQL-only suites: UUID semantics and advisory locks.
            if not postgres_ready:
                item.add_marker(skip_postgres)
        elif item.get_closest_marker("requires_database"):
            # SQLite-backed suites only need a writable DATABASE_PATH, which
            # this module guarantees; run them unconditionally.
            pass


_cache = {}


def _database_available_cached() -> bool:
    if "db" not in _cache:
        import asyncio

        _cache["db"] = asyncio.run(_database_available())
    return _cache["db"]
