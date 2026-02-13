import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    # Cached value 
    value: Any
    # Unix timestamp expiration
    expires_at: float

class QuoteCache:
    '''
    Simple in-memory cache with TTL.
    Goal: avoid repeated API calls when user presses "Show" and then "Send CSV", etc.
    '''
    def __init__(self, ttl_seconds: int = 45):
        self.ttl = ttl_seconds
        self._cache: dict[str, CacheEntry] = {}

    def get(self, key: str):
        # Get cached values
        entry = self._cache.get(key)
        if not entry:
            return None

        # Drop expired values
        if time.time() >= entry.expires_at:
            self._cache.pop(key, None)
            return None

        return entry.value
    
    def set(self, key: str, value):
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self.ttl
        )
