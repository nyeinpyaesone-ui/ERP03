from logging.config import fileConfig

import app.models  # noqa: F401 - register canonical ORM metadata
import sqlalchemy
from alembic import context
from app.core.config import settings
from app.db.base import Base
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

    # Canonical Alembic async dispatch (CLI path: `alembic upgrade head`).
    # Test provisioning shells out to this same CLI, so env.py never needs
    # an embedded-caller special case.
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
