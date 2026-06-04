import os
from typing import Protocol

from redis import asyncio as redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class AsyncRedisLike(Protocol):
    async def set(self, name: str, value: str, nx: bool = False, ex: int | None = None):
        ...

    async def delete(self, *names: str):
        ...

    async def aclose(self):
        ...


def get_redis_client() -> redis.Redis:
    return redis.from_url(REDIS_URL, decode_responses=True)
