from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import ConflictError, ForbiddenError
from app.services.supabase_identity import link_supabase_identity
from sqlalchemy.exc import IntegrityError


def _user(*, email="erp@example.test", supabase_user_id=None):
    return SimpleNamespace(
        id=uuid4(),
        email=email,
        supabase_user_id=supabase_user_id,
        active=True,
    )


@pytest.mark.asyncio
async def test_link_supabase_identity_requires_matching_verified_email():
    user = _user()
    session = SimpleNamespace(scalar=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock())

    with pytest.raises(ForbiddenError):
        await link_supabase_identity(session, user, uuid4(), "different@example.test")

    session.scalar.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_link_supabase_identity_persists_matching_identity():
    supabase_id = uuid4()
    user = _user(email=" ERP@Example.test ")
    session = SimpleNamespace(
        scalar=AsyncMock(side_effect=[user, None]),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    await link_supabase_identity(session, user, supabase_id, "erp@example.test")

    assert user.supabase_user_id == supabase_id
    session.scalar.assert_awaited()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_supabase_identity_cannot_be_linked_to_another_erp_user():
    supabase_id = uuid4()
    user = _user()
    other_user = _user()
    session = SimpleNamespace(
        scalar=AsyncMock(side_effect=[user, other_user]),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    with pytest.raises(ConflictError):
        await link_supabase_identity(session, user, supabase_id, "erp@example.test")

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_erp_user_cannot_replace_an_existing_supabase_identity():
    user = _user(supabase_user_id=uuid4())
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=user),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    with pytest.raises(ConflictError):
        await link_supabase_identity(session, user, uuid4(), "erp@example.test")

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_unique_identity_race_returns_conflict_not_server_error():
    user = _user()
    session = SimpleNamespace(
        scalar=AsyncMock(side_effect=[user, None]),
        commit=AsyncMock(side_effect=IntegrityError("insert", {}, RuntimeError("duplicate"))),
        rollback=AsyncMock(),
    )

    with pytest.raises(ConflictError, match="already linked"):
        await link_supabase_identity(session, user, uuid4(), "erp@example.test")

    session.rollback.assert_awaited_once()
