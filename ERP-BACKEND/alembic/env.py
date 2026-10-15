from logging.config import fileConfig

import app.models  # noqa: F401 - register canonical ORM metadata
from alembic import context
from alembic.runtime.environment import EnvironmentContext
from app.core.config import settings
from app.db.base import Base
import sqlalchemy
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

target_metadata = Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_migration_context_opts(sqlalchemy.make_url(settings.database_url).get_backend_name()),
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def _migration_context_opts(dialect_name: str) -> dict[str, bool]:
    """Dialect-aware Alembic options.

    SQLite cannot ALTER constraints in-place; enabling Alembic's batch mode
    (copy-and-move rebuild) makes the whole migration chain portable so the
    same schema evolves on both PostgreSQL and SQLite deployments.
    """
    opts: dict[str, bool] = {"compare_type": True, "compare_server_default": True}
    if dialect_name == "sqlite":
        opts["render_as_batch"] = True
    return opts


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        **_migration_context_opts(connection.dialect.name),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    import asyncio

    # Embedded invocation (pytest conftest provisions the test database by
    # executing this module from inside a running event loop): dispatching an
    # async engine here would raise "asyncio.run() cannot be called from a
    # running event loop". The embedded caller invokes `do_run_migrations`
    # directly on its own greenlet connection, so this must be a no-op.
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_async_migrations())  # CLI path: alembic upgrade head
    else:
        return


# A pre-installed proxy context marks an *embedded* caller (pytest conftest
# provisions the test database this way and drives `do_run_migrations`
# itself); only the standalone CLI runs the dispatch here. The check must be
# a call: `EnvironmentContext.get_current` is a classmethod, and referencing
# it without calling is always truthy.
_embedded = getattr(EnvironmentContext, "get_current", None)
if not (callable(_embedded) and _embedded() is not None):
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
