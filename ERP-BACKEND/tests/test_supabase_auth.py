from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import verify_supabase_access_token


@pytest.mark.asyncio
async def test_supabase_verification_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", None)
    monkeypatch.setattr(settings, "supabase_publishable_key", None)
    with pytest.raises(HTTPException) as exc:
        await verify_supabase_access_token("some-token")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_supabase_verification_rejects_unconfirmed_email(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(
        settings,
        "supabase_publishable_key",
        type("Secret", (), {"get_secret_value": lambda self: "public-key"})(),
    )
    response = httpx.Response(
        200,
        json={"id": "2d3d0000-0000-4000-8000-000000000001", "email": "user@example.com"},
    )
    client = AsyncMock()
    client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    context.__aexit__.return_value = False
    with (
        patch("app.core.security.httpx.AsyncClient", return_value=context),
        pytest.raises(HTTPException) as exc,
    ):
        await verify_supabase_access_token("unconfirmed-token")
    assert exc.value.status_code == 401
