import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

PER_MINUTE = 60
PER_DAY = 1000

# In-memory per-IP request timestamps; resets when the server restarts.
requests_by_ip: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    history = requests_by_ip[ip]

    while history and history[0] < now - 24 * 60 * 60:
        history.popleft()

    if len(history) >= PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {PER_DAY} requests per day. Try again later.",
        )

    last_minute = sum(1 for t in history if t > now - 60)
    if last_minute >= PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {PER_MINUTE} requests per minute. Try again later.",
        )

    history.append(now)
