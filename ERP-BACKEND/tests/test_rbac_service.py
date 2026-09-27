from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.identity import Base, Permission
from app.services.rbac import ensure_default_roles


@pytest.mark.asyncio
async def test_default_roles_fail_closed_when_permission_catalog_is_missing():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        with pytest.raises(RuntimeError, match="Missing permission catalog"):
            await ensure_default_roles(session, business_id=uuid4())

    await engine.dispose()
