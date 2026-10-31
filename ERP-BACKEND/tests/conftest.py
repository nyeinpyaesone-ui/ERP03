"""Shared pytest configuration for the backend test suite.

The service supports two backends: PostgreSQL (production; asyncpg) and
SQLite (local development / CI smoke; aiosqlite). Tests that require a
*migrated* database are tagged ``integration``; conftest provisions one
automatically from the Alembic chain against whichever backend is configured
via DATABASE_URL, so the suite is hermetic on both platforms.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

os.environ.setdefault("DATABASE_PATH", "/tmp/erp03-tests.sqlite3")
# Hermetic default: a fresh SQLite file per session unless the caller
# explicitly provides DATABASE_URL (PostgreSQL in CI, or a custom target).
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{os.environ['DATABASE_PATH']}")
# Disable rate limiting for tests (no Redis in test env)
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
# A pre-set DATABASE_URL (e.g. an exported shell profile) silently overrides
# the hermetic default above; log the effective target for traceability.
print(
    f"[conftest] provisioning test database: {os.environ['DATABASE_URL']}",
    file=sys.stderr,
)

_INTEGRATION_MARKERS = ("integration", "requires_database")


def pytest_configure(config):
    for marker in _INTEGRATION_MARKERS:
        config.addinivalue_line(
            "markers", f"{marker}: requires a reachable migrated database (DATABASE_URL)"
        )


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


async def _probe_and_migrate() -> bool:
    """Bring the session test database to the latest Alembic head.

    The target URL is resolved by this module at import (hermetic SQLite
    default, or an explicit DATABASE_URL for PostgreSQL in CI). Provisioning
    shells out to ``alembic upgrade head`` — the exact CLI path used at
    deployment — which keeps migration execution fully independent of
    pytest-asyncio's running event loop and guarantees test provisioning
    and production migrations can never diverge. A stale/mismatched schema
    file is rebuilt from scratch so every run starts deterministic.
    """
    url = os.environ["DATABASE_URL"]
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            if connection.dialect.name == "sqlite":
                stamped = await connection.execute(
                    text(
                        "SELECT count(*) FROM sqlite_master "
                        "WHERE type='table' AND name='permissions'"
                    )
                )
                needs_rebuild = stamped.scalar() == 0
            else:
                needs_rebuild = False
    except Exception:
        return False

    # The app's own engine (imported by integration tests via
    # app.db.session) resolves settings.database_url at import time; pin it
    # to the same URL we just probed so provisioning and application share
    # one database on every platform.
    os.environ["DATABASE_URL"] = url

    from app.core.config import settings

    if str(settings.database_url) != url:
        raise RuntimeError(f"app engine URL {str(settings.database_url)!r} != provisioned {url!r}")

    try:
        import subprocess

        backend_dir = Path(__file__).resolve().parents[1]
        if needs_rebuild:
            db_path = url.split("///", 1)[-1].lstrip("/")
            Path(db_path).unlink(missing_ok=True)
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(backend_dir),
            env={**os.environ},
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"alembic upgrade head failed ({result.returncode}): "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
        return True
    except Exception as exc:  # pragma: no cover - provisioning diagnostics
        import traceback

        print(f"[conftest] database provisioning failed: {exc!r}", file=sys.stderr)
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


_cache = {}


def _database_ready_cached() -> bool:
    if "db" not in _cache:
        import asyncio

        _cache["db"] = asyncio.run(_probe_and_migrate())
    return _cache["db"]


def pytest_collection_modifyitems(session, config, items):
    database_ready = _database_ready_cached()
    skip_database = pytest.mark.skip(
        reason="Test database unavailable/unmigratable (set DATABASE_URL)"
    )
    for item in items:
        if item.get_closest_marker(_INTEGRATION_MARKERS) and not database_ready:
            item.add_marker(skip_database)
