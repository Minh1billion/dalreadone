import json
from typing import Any

import redis as syncredis
import redis.asyncio as aioredis

from app.core.config import Config


_async_client: aioredis.Redis | None = None
_sync_client: syncredis.Redis | None = None


def get_async_client() -> aioredis.Redis:
    global _async_client
    if _async_client is None:
        _async_client = aioredis.from_url(
            Config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _async_client


def get_sync_client() -> syncredis.Redis:
    global _sync_client
    if _sync_client is None:
        _sync_client = syncredis.from_url(
            Config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _sync_client


def _key(namespace: str, id: str) -> str:
    return f"{namespace}:{id}"


def set(namespace: str, id: str, value: Any, ttl: int | None = None) -> None:
    r = get_sync_client()
    raw = json.dumps(value, default=str)
    if ttl:
        r.setex(_key(namespace, id), ttl, raw)
    else:
        r.set(_key(namespace, id), raw)


def get(namespace: str, id: str) -> Any | None:
    raw = get_sync_client().get(_key(namespace, id))
    return json.loads(raw) if raw is not None else None


def delete(namespace: str, id: str) -> None:
    get_sync_client().delete(_key(namespace, id))


def exists(namespace: str, id: str) -> bool:
    return bool(get_sync_client().exists(_key(namespace, id)))


async def async_set(namespace: str, id: str, value: Any, ttl: int | None = None) -> None:
    r = get_async_client()
    raw = json.dumps(value, default=str)
    if ttl:
        await r.setex(_key(namespace, id), ttl, raw)
    else:
        await r.set(_key(namespace, id), raw)


async def async_get(namespace: str, id: str) -> Any | None:
    raw = await get_async_client().get(_key(namespace, id))
    return json.loads(raw) if raw is not None else None


async def async_delete(namespace: str, id: str) -> None:
    await get_async_client().delete(_key(namespace, id))


async def async_exists(namespace: str, id: str) -> bool:
    return bool(await get_async_client().exists(_key(namespace, id)))