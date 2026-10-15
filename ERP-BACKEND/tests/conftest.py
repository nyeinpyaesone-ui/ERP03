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
    """Verify DATABASE_URL is reachable and bring it to the latest head.

    Running the real migration chain here makes integration tests exercise
    the same schema as production (including seeded permissions), on either
    PostgreSQL or SQLite. The project's own ``alembic/env.py`` is reused so
    test provisioning and deployment migrations can never diverge; it runs
    through ``run_sync`` inside the *current* event loop (no nested loops).
    """
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://erp03:erp03@postgres:5432/erp03",
    )
    try:
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return False

    try:
        import logging

        logging.getLogger("alembic").handlers.clear()  # keep pytest capture clean

        from pathlib import Path as _Path

        import importlib.util

        from alembic.config import Config as AlembicConfig
        from alembic.runtime.environment import EnvironmentContext
        from alembic.script import ScriptDirectory

        backend_dir = _Path(__file__).resolve().parents[1]
        config = AlembicConfig(str(backend_dir / "alembic.ini"))
        config.set_main_option("script_location", str(backend_dir / "alembic"))

        # Load the project's own env.py (it is a script, not an importable
        # module) so test provisioning and deployment migrations never diverge.
        spec = importlib.util.spec_from_file_location(
            "erp03_alembic_env", str(backend_dir / "alembic" / "env.py")
        )
        env_module = importlib.util.module_from_spec(spec)

        def _load_and_run(sync_connection) -> None:
            script = ScriptDirectory.from_config(config)

            # Phase 1: install a proxy-backed EnvironmentContext *before*
            # executing env.py, because env.py reads `context.config` at
            # module level. Its bottom dispatch detects the proxy context and
            # stays inert, so nothing runs against a second engine here.
            with EnvironmentContext(config, script):
                spec.loader.exec_module(env_module)

            # Phase 2: run the full migration chain on THIS greenlet-bound
            # connection — identical wiring to the CLI async path, which
            # invokes do_run_migrations inside the live EnvironmentContext
            # created by `alembic upgrade`. The fn= hook receives our
            # connection; do_run_migrations then calls context.configure(
            # connection=...) itself and executes every upgrade step.
            with EnvironmentContext(
                config, script, fn=env_module.do_run_migrations, connection=sync_connection
            ) as ec:
                ec.run_migrations()

        await connection.run_sync(_load_and_run)
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
        if item.get_closest_marker(_INTEGRATION_MARKERS):
            if not database_ready:
                item.add_marker(skip_database)
