"""Request-scoped SQLAlchemy unit-of-work commit/rollback behavior."""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import session as session_module


@pytest.mark.asyncio
async def test_request_session_commits_on_success_and_rolls_back_on_error(
    tmp_path, monkeypatch
):
    """CRUD routers that only flush must persist only successful requests."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'unit-of-work.sqlite3'}")
    metadata = MetaData()
    entries = Table(
        "request_unit_of_work",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("value", String(40), nullable=False, unique=True),
    )
    try:
        async with engine.begin() as connection:
            await connection.run_sync(metadata.create_all)

        factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
        monkeypatch.setattr(session_module, "SessionFactory", factory)

        successful_request = session_module.get_db_session()
        successful_session = await anext(successful_request)
        await successful_session.execute(insert(entries).values(value="persisted"))
        with pytest.raises(StopAsyncIteration):
            await anext(successful_request)

        failed_request = session_module.get_db_session()
        failed_session = await anext(failed_request)
        await failed_session.execute(insert(entries).values(value="rolled-back"))
        with pytest.raises(RuntimeError, match="handler failure"):
            await failed_request.athrow(RuntimeError("handler failure"))

        async with engine.connect() as connection:
            values = (
                await connection.execute(select(entries.c.value).order_by(entries.c.value))
            ).scalars().all()

        assert values == ["persisted"]
    finally:
        await engine.dispose()
