"""Coverage for the Redis-backed rate limiter's IP resolution and hygiene."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from app.core.config import settings
from app.main import RedisRateLimitMiddleware


async def _noop_app(scope, receive, send):
    return None


def _middleware_with_mocked_redis():
    redis_client = AsyncMock()
    pipeline = MagicMock()
    pipeline.zremrangebyscore = AsyncMock()
    pipeline.zcard = AsyncMock()
    pipeline.zadd = AsyncMock()
    pipeline.expire = AsyncMock()
    pipeline.execute = AsyncMock(return_value=[None, 0])
    redis_client.pipeline = MagicMock(return_value=pipeline)
    middleware = RedisRateLimitMiddleware(_noop_app, redis_url="redis://localhost:6379/0")
    middleware.redis = redis_client
    return middleware, pipeline


async def _rate_limit_key_for_token(token: str) -> str:
    middleware, pipeline = _middleware_with_mocked_redis()
    scope = {
        "type": "http",
        "client": ("192.0.2.10", 0),
        "headers": [(b"authorization", f"Bearer {token}".encode())],
    }
    await middleware(scope, None, None)
    return pipeline.zadd.call_args.args[0]


def test_redis_client_uses_bounded_pool_and_fail_fast_timeouts():
    with patch("redis.asyncio.from_url") as mock_redis:
        RedisRateLimitMiddleware(_noop_app, redis_url="redis://localhost:6379/0")

        mock_redis.assert_called_once_with(
            "redis://localhost:6379/0",
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
            health_check_interval=30,
        )


@pytest.mark.asyncio
async def test_close_releases_redis_connection_pool():
    with patch("redis.asyncio.from_url") as mock_redis:
        redis_client = AsyncMock()
        mock_redis.return_value = redis_client

        middleware = RedisRateLimitMiddleware(_noop_app, redis_url="redis://localhost:6379/0")
        await middleware.close()

        redis_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_xff_ignored_from_untrusted_peer():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 0])
        mock_redis_instance.pipeline = MagicMock(return_value=mock_pipeline)

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
        mock_pipeline.zadd.assert_called()
        args, _ = mock_pipeline.zadd.call_args
        assert "1.2.3.4" in str(args)


@pytest.mark.asyncio
async def test_xff_honoured_from_trusted_proxy():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 0])
        mock_redis_instance.pipeline = MagicMock(return_value=mock_pipeline)

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
        mock_pipeline.zadd.assert_called()
        args, _ = mock_pipeline.zadd.call_args
        assert "9.9.9.9" in str(args)


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_threshold():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance
        # First call returns count=1, second call returns count=2 (exceeds limit)
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(
            side_effect=[
                [None, 1],  # First request: count=1
                [None, 2],  # Second request: count=2
                [None, 3],  # Third request: count=3 (exceeds limit of 2)
            ]
        )
        mock_redis_instance.pipeline = MagicMock(return_value=mock_pipeline)

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


@pytest.mark.asyncio
async def test_verified_unexpired_jwt_selects_canonical_tenant_bucket():
    tenant_id = "11111111-1111-1111-1111-111111111111"
    token = jwt.encode(
        {"business_id": tenant_id, "exp": int(time.time()) + 300},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == f"ratelimit:{tenant_id}"


@pytest.mark.asyncio
async def test_forged_jwt_falls_back_to_client_ip_bucket():
    token = jwt.encode(
        {
            "business_id": "11111111-1111-1111-1111-111111111111",
            "exp": int(time.time()) + 300,
        },
        "attacker-controlled-key",
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == "ratelimit:192.0.2.10"


@pytest.mark.asyncio
async def test_expired_jwt_falls_back_to_client_ip_bucket():
    token = jwt.encode(
        {
            "business_id": "11111111-1111-1111-1111-111111111111",
            "exp": int(time.time()) - 60,
        },
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == "ratelimit:192.0.2.10"


@pytest.mark.asyncio
async def test_jwt_without_expiry_falls_back_to_client_ip_bucket():
    token = jwt.encode(
        {"business_id": "11111111-1111-1111-1111-111111111111"},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == "ratelimit:192.0.2.10"


@pytest.mark.asyncio
async def test_jwt_with_malformed_tenant_id_falls_back_to_client_ip_bucket():
    token = jwt.encode(
        {"business_id": "not-a-uuid", "exp": int(time.time()) + 300},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == "ratelimit:192.0.2.10"


@pytest.mark.asyncio
async def test_jwt_without_business_id_falls_back_to_client_ip_bucket():
    token = jwt.encode(
        {"exp": int(time.time()) + 300},
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    assert await _rate_limit_key_for_token(token) == "ratelimit:192.0.2.10"
