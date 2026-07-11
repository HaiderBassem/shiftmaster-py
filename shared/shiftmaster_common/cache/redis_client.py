"""
Redis client lifecycle and caching/rate-limiting helpers.

Lifecycle
---------
Call `init_redis()` in the FastAPI lifespan startup and
`close_redis()` in shutdown. The module-level `redis` variable
is then available everywhere via `get_redis()`.

Rate Limiting
-------------
`rate_limit_check(key, max_requests, window_seconds)` implements a
sliding-window counter using Redis INCR + EXPIRE. Returns True when the
caller has exceeded the limit.

    Typical usage (in a router/dependency):
        from shiftmaster_common.cache.redis_client import get_redis, rate_limit_check
        ...
        exceeded = await rate_limit_check(
            key=f"login:attempt:{client_ip}",
            max_requests=5,
            window_seconds=300,   # 5 attempts per 5 minutes
        )
        if exceeded:
            raise HTTPException(429, "Too many login attempts")

Caching
-------
`cache_get` / `cache_set` / `cache_delete` — thin wrappers that handle
JSON serialisation and a consistent key namespace.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

from shiftmaster_common.logging.structured import get_logger

logger = get_logger(__name__)

# Module-level singleton — initialised in lifespan, cleared on shutdown
_redis: Redis | None = None


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def init_redis(url: str) -> Redis:
    """Create the Redis connection pool and verify connectivity."""
    global _redis
    _redis = aioredis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )
    # Verify connection on startup
    await _redis.ping()
    logger.info("redis.connected", url=url)
    return _redis


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        logger.info("redis.disconnected")


def get_redis() -> Redis:
    """
    Return the active Redis client.
    Raises RuntimeError if `init_redis()` was never called.
    """
    if _redis is None:
        raise RuntimeError("Redis is not initialised. Call init_redis() first.")
    return _redis


# ── Rate limiting ─────────────────────────────────────────────────────────────

async def rate_limit_check(
    key: str,
    max_requests: int,
    window_seconds: int,
) -> bool:
    """
    Sliding-window rate limiter backed by Redis.

    Returns True  → limit exceeded (caller should raise 429)
    Returns False → request is within the allowed rate
    """
    client = get_redis()
    full_key = f"ratelimit:{key}"

    pipe = client.pipeline()
    pipe.incr(full_key)
    pipe.expire(full_key, window_seconds)
    results = await pipe.execute()

    current_count: int = results[0]
    exceeded = current_count > max_requests

    if exceeded:
        logger.warning(
            "rate_limit.exceeded",
            key=key,
            count=current_count,
            max_requests=max_requests,
        )
    return exceeded


async def rate_limit_reset(key: str) -> None:
    """Reset the counter for *key* (e.g. on successful login)."""
    await get_redis().delete(f"ratelimit:{key}")


# ── Idempotency ───────────────────────────────────────────────────────────────

async def check_idempotency(key: str, ttl_seconds: int = 604800) -> bool:
    """
    Check if an event has already been processed using Redis SETNX.
    Returns True if the event was ALREADY processed.
    Returns False if the event is NEW and sets the key with a TTL (default 7 days).
    """
    client = get_redis()
    full_key = f"idempotency:{key}"
    
    # setnx returns True if key was set (i.e., new event), False if it existed
    is_new = await client.set(full_key, "1", ex=ttl_seconds, nx=True)
    
    if not is_new:
        logger.debug("idempotency.hit", key=key)
        return True
    return False


# ── Generic JSON cache ────────────────────────────────────────────────────────

_CACHE_PREFIX = "cache:"


async def cache_get(key: str) -> Any | None:
    """Return the cached value for *key*, or None if absent/expired."""
    raw = await get_redis().get(f"{_CACHE_PREFIX}{key}")
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("cache.decode_error", key=key)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Serialise *value* to JSON and store under *key* with a TTL."""
    await get_redis().setex(
        f"{_CACHE_PREFIX}{key}",
        ttl_seconds,
        json.dumps(value, default=str),
    )


async def cache_delete(key: str) -> None:
    """Evict *key* from the cache."""
    await get_redis().delete(f"{_CACHE_PREFIX}{key}")


async def cache_delete_pattern(pattern: str) -> int:
    """
    Evict all keys matching a glob *pattern* (e.g. "employee:*").
    Returns the number of deleted keys.

    Use sparingly — SCAN-based, but still O(N) on large key spaces.
    """
    client = get_redis()
    full_pattern = f"{_CACHE_PREFIX}{pattern}"
    deleted = 0
    async for key in client.scan_iter(match=full_pattern, count=100):
        await client.delete(key)
        deleted += 1
    if deleted:
        logger.info("cache.invalidated", pattern=pattern, count=deleted)
    return deleted
