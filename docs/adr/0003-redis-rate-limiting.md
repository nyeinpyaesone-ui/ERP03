# ADR-0003: Redis-Backed Rate Limiting

## Status

Accepted

## Context

The application needs distributed rate limiting across multiple workers. In-memory rate limiting doesn't work with multiple processes/containers.

## Decision

Use Redis sorted sets (ZSET) for sliding window rate limiting:
- `ZREMRANGEBYSCORE` for window cleanup
- `ZCARD` for count
- `ZADD` + `EXPIRE` for request recording
- Configurable via `rate_limit_enabled`, `rate_limit_requests`, `rate_limit_window`
- Trusted proxy support via `X-Forwarded-For`

## Consequences

- **Positive**: Distributed, accurate, works across workers
- **Negative**: Requires Redis infrastructure
- **Mitigation**: Graceful degradation when Redis unavailable (tests use fakeredis)

## Alternatives Considered

- In-memory sliding window: Rejected — doesn't work across workers
- Token bucket: Rejected — less accurate for burst protection
- Fixed window: Rejected — boundary burst problem
