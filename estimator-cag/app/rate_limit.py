from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitDecision:
    limit: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def enforce(self, *, key: str, limit: int, window_seconds: int = 60) -> RateLimitDecision | None:
        now = time.time()
        events = self._events[key]
        while events and now - events[0] >= window_seconds:
            events.popleft()
        if len(events) >= limit:
            retry_after = max(1, int(window_seconds - (now - events[0])))
            return RateLimitDecision(limit=limit, retry_after_seconds=retry_after)
        events.append(now)
        return None


limiter = InMemoryRateLimiter()


def _rate_limit_key(request: Request, x_api_key: str) -> str:
    if x_api_key:
        return x_api_key
    if request.client and request.client.host:
        return request.client.host
    return "anonymous"


def enforce_rate_limit(
    *,
    request: Request,
    x_api_key: str,
    limit: int,
    namespace: str,
) -> None:
    key = f"{namespace}:{_rate_limit_key(request, x_api_key)}"
    decision = limiter.enforce(key=key, limit=limit)
    if decision is None:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "rate_limit_exceeded",
            "limit": f"{decision.limit}/minute",
            "retry_after_seconds": decision.retry_after_seconds,
        },
        headers={"Retry-After": str(decision.retry_after_seconds)},
    )
