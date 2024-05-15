"""Least-recently-used cache built on ``OrderedDict``."""

from collections import OrderedDict


class LRUCache:
    """Fixed-capacity cache that evicts the least recently used entry.

    Both ``get`` and ``put`` move the key to the "most recent" end.

    >>> cache = LRUCache(2)
    >>> cache.put("a", 1)
    >>> cache.put("b", 2)
    >>> cache.get("a")
    1
    >>> cache.put("c", 3)
    >>> cache.get("b") is None
    True
    >>> len(cache)
    2
    """

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._entries = OrderedDict()

    def __len__(self):
        return len(self._entries)

    def get(self, key):
        if key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key]

    def put(self, key, value):
        self._entries[key] = value
        self._entries.move_to_end(key)
        if len(self._entries) > self._capacity:
            self._entries.popitem(last=False)
