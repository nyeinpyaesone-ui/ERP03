from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.core.config import settings
from app.core.security import verify_supabase_access_token
from fastapi import HTTPException


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

@pytest.mark.asyncio
async def test_local_supabase_signup_token_is_accepted_by_backend(monkeypatch):
    """Exercise the real local GoTrue endpoint and the backend's token verifier."""
    import os
    from uuid import uuid4

    if os.getenv("SUPABASE_AUTH_INTEGRATION") != "true":
        pytest.skip("local Supabase Auth integration job only")

    supabase_url = os.environ["SUPABASE_URL"]
    publishable_key = os.environ["SUPABASE_PUBLISHABLE_KEY"]
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(
        settings,
        "supabase_publishable_key",
        type("Secret", (), {"get_secret_value": lambda self: publishable_key})(),
    )

    email = f"erp03-ci-{uuid4().hex}@example.test"
    password = f"Ci-Only-{uuid4().hex}-A9!"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{supabase_url.rstrip('/')}/auth/v1/signup",
            headers={"apikey": publishable_key},
            json={"email": email, "password": password},
        )
    assert response.status_code in {200, 201}, response.text
    access_token = response.json().get("access_token")
    assert access_token, "local Supabase signup did not return an access token"

    identity = await verify_supabase_access_token(access_token)
    assert identity["email"].casefold() == email.casefold()
    assert identity.get("email_confirmed_at")


@pytest.mark.asyncio
async def test_local_supabase_rejects_invalid_access_token(monkeypatch):
    """Ensure the backend fails closed against the running local Auth service."""
    import os

    if os.getenv("SUPABASE_AUTH_INTEGRATION") != "true":
        pytest.skip("local Supabase Auth integration job only")

    supabase_url = os.environ["SUPABASE_URL"]
    publishable_key = os.environ["SUPABASE_PUBLISHABLE_KEY"]
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(
        settings,
        "supabase_publishable_key",
        type("Secret", (), {"get_secret_value": lambda self: publishable_key})(),
    )

    with pytest.raises(HTTPException) as exc:
        await verify_supabase_access_token("invalid-local-supabase-token")
    assert exc.value.status_code == 401
