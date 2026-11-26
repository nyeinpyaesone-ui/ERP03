from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import httpx
import jwt
import pytest

from app.core import security
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import SecretStr


@pytest.mark.asyncio
async def test_supabase_verification_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.setattr(security.security.settings, "supabase_url", None)
    monkeypatch.setattr(security.security.settings, "supabase_publishable_key", None)
    with pytest.raises(HTTPException) as exc:
        await security.verify_supabase_access_token("some-token")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_supabase_verification_requires_confirmed_email(monkeypatch):
    monkeypatch.setattr(security.security.settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(security.security.settings, "supabase_publishable_key", SecretStr("public-key"))
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "id": "2d3d0000-0000-4000-8000-000000000001",
                "email": "user@example.com",
            },
            request=request,
        )
    )
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        security.httpx,
        "AsyncClient",
        lambda **kwargs: original_client(transport=transport, **kwargs),
    )
    with pytest.raises(HTTPException) as exc:
        await security.verify_supabase_access_token("unconfirmed-token")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_supabase_verification_accepts_confirmed_identity(monkeypatch):
    monkeypatch.setattr(security.security.settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(security.security.settings, "supabase_publishable_key", SecretStr("public-key"))
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "id": "2d3d0000-0000-4000-8000-000000000001",
                "email": "user@example.com",
                "email_confirmed_at": "2026-11-26T00:00:00Z",
            },
            request=request,
        )
    )
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        security.httpx,
        "AsyncClient",
        lambda **kwargs: original_client(transport=transport, **kwargs),
    )
    identity = await security.verify_supabase_access_token("valid-token")
    assert identity["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_supabase_claims_are_derived_from_linked_erp_user(monkeypatch):
    user = SimpleNamespace(
        id=UUID("12345678-1234-1234-1234-123456789abc"),
        business_id=UUID("12345678-1234-1234-1234-123456789abd"),
        branch_id=None,
        email="user@example.com",
        display_name="ERP User",
    )
    session = SimpleNamespace(scalar=AsyncMock(return_value=user))
    monkeypatch.setattr(security.security.settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(
        security,
        "decode_access_token",
        lambda token: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="Invalid or expired access token")
        ),
    )
    monkeypatch.setattr(
        security,
        "verify_supabase_access_token",
        AsyncMock(
            return_value={
                "id": "2d3d0000-0000-4000-8000-000000000001",
                "email": "user@example.com",
                "email_confirmed_at": "2026-11-26T00:00:00Z",
            }
        ),
    )
    token = jwt.encode(
        {"iss": "https://example.supabase.co/auth/v1"},
        "not-used-for-verification",
        algorithm="HS256",
    )
    claims = await security.current_claims(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        session,
    )
    assert claims["sub"] == str(user.id)
    assert claims["business_id"] == str(user.business_id)
    assert claims["branch_id"] is None
    assert claims["auth_provider"] == "supabase"
