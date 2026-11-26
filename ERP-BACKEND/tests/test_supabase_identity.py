from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import ConflictError, ForbiddenError
from app.services.supabase_identity import link_supabase_identity



@pytest.mark.asyncio
async def test_link_supabase_identity_requires_matching_verified_email():
    user = SimpleNamespace(id=uuid4(), email="erp@example.test", supabase_user_id=None)
    session = SimpleNamespace(scalar=AsyncMock(return_value=None), commit=AsyncMock())

    with pytest.raises(ForbiddenError):
        await link_supabase_identity(
            session, user, uuid4(), "different@example.test"
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_link_supabase_identity_persists_matching_identity():
    supabase_id = uuid4()
    user = SimpleNamespace(
        id=uuid4(), email=" ERP@Example.test ", supabase_user_id=None
    )
    session = SimpleNamespace(scalar=AsyncMock(return_value=None), commit=AsyncMock())

    await link_supabase_identity(session, user, supabase_id, "erp@example.test")

    assert user.supabase_user_id == supabase_id
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_supabase_identity_cannot_be_linked_to_another_erp_user():
    supabase_id = uuid4()
    user = SimpleNamespace(id=uuid4(), email="erp@example.test", supabase_user_id=None)
    other_user = SimpleNamespace(id=uuid4())
    session = SimpleNamespace(scalar=AsyncMock(return_value=other_user), commit=AsyncMock())

    with pytest.raises(ConflictError):
        await link_supabase_identity(session, user, supabase_id, "erp@example.test")

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_erp_user_cannot_replace_an_existing_supabase_identity():
    user = SimpleNamespace(
        id=uuid4(), email="erp@example.test", supabase_user_id=uuid4()
    )
    session = SimpleNamespace(scalar=AsyncMock(return_value=None), commit=AsyncMock())

    with pytest.raises(ConflictError):
        await link_supabase_identity(session, user, uuid4(), "erp@example.test")

    session.commit.assert_not_awaited()
