"""Coverage for the Redis-backed rate limiter's IP resolution and hygiene."""

from unittest.mock import AsyncMock, patch

import pytest
from app.main import RedisRateLimitMiddleware


async def _noop_app(scope, receive, send):
    return None


@pytest.mark.asyncio
async def test_xff_ignored_from_untrusted_peer():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.pipeline.return_value = AsyncMock()
        mock_redis_instance.pipeline.return_value.execute = AsyncMock(return_value=[None, 0])

        mw = RedisRateLimitMiddleware(
            _noop_app, redis_url="redis://localhost:6379/0", trusted_proxies=set()
        )
        mw.redis = mock_redis_instance
        scope = {
            "type": "http",
            "client": ("1.2.3.4", 0),
            "headers": [(b"x-forwarded-for", b"9.9.9.9")],
        }
        await mw(scope, None, None)
        # Verify XFF from untrusted peer is ignored
        mock_redis_instance.zadd.assert_called()
        args, _ = mock_redis_instance.zadd.call_args
        assert "1.2.3.4" in str(args)


@pytest.mark.asyncio
async def test_xff_honoured_from_trusted_proxy():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.pipeline.return_value = AsyncMock()
        mock_redis_instance.pipeline.return_value.execute = AsyncMock(return_value=[None, 0])

        mw = RedisRateLimitMiddleware(
            _noop_app, redis_url="redis://localhost:6379/0", trusted_proxies={"1.2.3.4"}
        )
        mw.redis = mock_redis_instance
        scope = {
            "type": "http",
            "client": ("1.2.3.4", 0),
            "headers": [(b"x-forwarded-for", b"9.9.9.9, 10.0.0.1")],
        }
        await mw(scope, None, None)
        # Verify XFF from trusted proxy is honoured
        mock_redis_instance.zadd.assert_called()
        args, _ = mock_redis_instance.zadd.call_args
        assert "9.9.9.9" in str(args)


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_threshold():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        # First call returns count=1, second call returns count=2 (exceeds limit)
        mock_redis_instance.pipeline.return_value = AsyncMock()
        mock_redis_instance.pipeline.return_value.execute = AsyncMock(
            side_effect=[
                [None, 1],  # First request: count=1
                [None, 2],  # Second request: count=2
                [None, 3],  # Third request: count=3 (exceeds limit of 2)
            ]
        )

        mw = RedisRateLimitMiddleware(
            _noop_app,
            redis_url="redis://localhost:6379/0",
            requests_per_window=2,
            window_seconds=60,
        )
        mw.redis = mock_redis_instance
        scope = {"type": "http", "client": ("5.5.5.5", 0), "headers": []}

        statuses = []

        async def capture_send(message):
            statuses.append(message.get("status"))

        for _ in range(2):
            await mw(scope, None, capture_send)
        statuses.clear()
        await mw(scope, None, capture_send)
        assert 429 in statuses
