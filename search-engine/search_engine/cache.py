"""Phase 3: query result cache. Start with a plain LRU (functools.lru_cache
or a small dict + OrderedDict), then benchmark hit/miss latency for your
resume numbers -- this is where you can generate the classic
"42ms -> 3ms" style result.
"""
from collections import OrderedDict
from typing import Any


class LRUCache:
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self._store: "OrderedDict[str, Any]" = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)
