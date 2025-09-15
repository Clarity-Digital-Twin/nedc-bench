from __future__ import annotations

import asyncio
import time
from typing import Dict, List

from fastapi import HTTPException, Request


class RateLimiter:
    """Simple in-memory rate limiter per client id."""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str) -> bool:
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            window = self.requests.setdefault(client_id, [])
            # Drop old
            self.requests[client_id] = [t for t in window if t > minute_ago]
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            self.requests[client_id].append(now)
            return True


rate_limiter = RateLimiter(requests_per_minute=100)


async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "anonymous"
    allowed = await rate_limiter.check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": "60"})
    return await call_next(request)

