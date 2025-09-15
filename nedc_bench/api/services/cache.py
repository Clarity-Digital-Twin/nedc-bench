from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any

from redis import asyncio as aioredis

from nedc_bench import PACKAGE_VERSION

logger = logging.getLogger(__name__)


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class RedisCache:
    """Thin async Redis JSON cache with TTL.

    Fails open: cache ops are best-effort and never raise to callers.
    """

    def __init__(self, url: str | None = None, ttl_seconds: int | None = None) -> None:
        self.url = url or os.environ.get("REDIS_URL", "redis://redis:6379")
        self.ttl_seconds = ttl_seconds or int(os.environ.get("CACHE_TTL_SECONDS", "86400"))
        try:
            # The redis asyncio client is untyped; cast to Any for mypy.
            self._client = aioredis.from_url(self.url, decode_responses=True)  # type: ignore[no-untyped-call]
        except Exception as exc:  # pragma: no cover - construction should not fail
            logger.warning("Redis client init failed: %s", exc)
            self._client = None

    async def ping(self) -> bool:
        try:
            if self._client is None:
                return False
            return await self._client.ping()  # type: ignore[no-any-return]
        except Exception:
            return False

    async def get_json(self, key: str) -> Any | None:
        try:
            if self._client is None:
                return None
            raw = await self._client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:
            logger.debug("Cache get failed for %s: %s", key, exc)
            return None

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            if self._client is None:
                return
            payload = json.dumps(value, default=_json_default)
            await self._client.set(key, payload, ex=ttl or self.ttl_seconds)
        except Exception as exc:
            logger.debug("Cache set failed for %s: %s", key, exc)

    @staticmethod
    def make_key(
        ref_bytes: bytes,
        hyp_bytes: bytes,
        algorithm: str,
        pipeline: str,
        version: str | None = None,
    ) -> str:
        version_str = version or PACKAGE_VERSION
        h = sha256()
        # Use separators to avoid ambiguity
        h.update(ref_bytes)
        h.update(b"|")
        h.update(hyp_bytes)
        h.update(b"|")
        h.update(algorithm.encode("utf-8"))
        h.update(b"|")
        h.update(pipeline.encode("utf-8"))
        h.update(b"|")
        h.update(version_str.encode("utf-8"))
        return f"nedc:{algorithm}:{pipeline}:{h.hexdigest()}"


# Singleton cache instance
redis_cache = RedisCache()
