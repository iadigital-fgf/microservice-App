import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis.asyncio as aioredis

from fgf_service.core.config import settings

logger = logging.getLogger(__name__)

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def cache_get(key: str) -> Any | None:
    try:
        client = get_redis()
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception as exc:
        logger.warning("Redis GET falló para '%s': %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    try:
        client = get_redis()
        await client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or settings.redis_ttl_seconds,
        )
    except Exception as exc:
        logger.warning("Redis SET falló para '%s': %s", key, exc)


async def cache_delete(key: str) -> None:
    try:
        client = get_redis()
        await client.delete(key)
    except Exception as exc:
        logger.warning("Redis DELETE falló para '%s': %s", key, exc)


def cached(key_prefix: str, ttl: int | None = None) -> Callable:
    """Decorator para cachear el resultado de una función async."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{key_prefix}:{':'.join(str(v) for v in list(args) + list(kwargs.values()))}"
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                logger.debug("Cache HIT: %s", cache_key)
                return cached_value
            result = await func(*args, **kwargs)
            await cache_set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
