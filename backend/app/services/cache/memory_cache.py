import time
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict

class MemoryCache:
    """
    Thread-safe in-memory Least Recently Used (LRU) cache with Time-To-Live (TTL).
    Provides microsecond-level query caching for vector searches and repetitive audit retrievals.
    """
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from cache if not expired.
        Promotes the item to most recently used.
        """
        now = time.time()
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expire_at = self._cache[key]
            if expire_at is not None and now > expire_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Hit: mark as recently used
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Sets a cache key with optional TTL (in seconds).
        Evicts the oldest entry if max_size is reached.
        """
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else None

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expire_at)

            # Evict least recently used if exceeding maximum capacity
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

    def invalidate(self, key: str) -> bool:
        """Removes a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Flushes the cache."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Returns the number of active entries."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_ratio": round(hit_ratio, 3)
            }

# Global cache singletons
query_cache = MemoryCache(max_size=500, default_ttl=300)
audit_cache = MemoryCache(max_size=200, default_ttl=600)
