"""Coverage for the in-memory rate limiter's IP resolution and hygiene."""

import pytest
from app.main import RateLimitMiddleware


async def _noop_app(scope, receive, send):
    return None


@pytest.mark.asyncio
async def test_xff_ignored_from_untrusted_peer():
    mw = RateLimitMiddleware(_noop_app, trusted_proxies=set())
    scope = {
        "type": "http",
        "client": ("1.2.3.4", 0),
        "headers": [(b"x-forwarded-for", b"9.9.9.9")],
    }
    await mw(scope, None, None)
    assert "1.2.3.4" in mw.requests
    assert "9.9.9.9" not in mw.requests


@pytest.mark.asyncio
async def test_xff_honoured_from_trusted_proxy():
    mw = RateLimitMiddleware(_noop_app, trusted_proxies={"1.2.3.4"})
    scope = {
        "type": "http",
        "client": ("1.2.3.4", 0),
        "headers": [(b"x-forwarded-for", b"9.9.9.9, 10.0.0.1")],
    }
    await mw(scope, None, None)
    assert "9.9.9.9" in mw.requests
    assert "1.2.3.4" not in mw.requests


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_threshold():
    mw = RateLimitMiddleware(_noop_app, requests_per_window=2, window_seconds=60)
    scope = {"type": "http", "client": ("5.5.5.5", 0), "headers": []}

    statuses = []

    async def capture_send(message):
        statuses.append(message.get("status"))

    for _ in range(2):
        await mw(scope, None, capture_send)
    statuses.clear()
    await mw(scope, None, capture_send)
    assert 429 in statuses
