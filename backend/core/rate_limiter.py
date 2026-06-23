"""
In-memory sliding-window rate limiter.
In production, swap the dict for Redis with pipeline atomicity.
"""
import time
from collections import defaultdict, deque
from core.config import settings


class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.limit = requests_per_minute
        self.window = 60          # seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    async def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets[key]

        # Evict timestamps outside the window
        while bucket and bucket[0] < now - self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            return False

        bucket.append(now)
        return True

    async def remaining(self, key: str) -> int:
        now = time.monotonic()
        bucket = self._buckets[key]
        while bucket and bucket[0] < now - self.window:
            bucket.popleft()
        return max(0, self.limit - len(bucket))
