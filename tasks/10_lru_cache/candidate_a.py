"""A small cache with a size limit."""


class LRUCache:
    """Cache that drops the oldest entry once it is full.

    >>> cache = LRUCache(2)
    >>> cache.put("a", 1)
    >>> cache.get("a")
    1
    >>> cache.get("missing") is None
    True
    """

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self.entries = {}

    def __len__(self):
        return len(self.entries)

    def get(self, key):
        return self.entries.get(key)

    def put(self, key, value):
        self.entries[key] = value
        if len(self.entries) > self.capacity:
            oldest = next(iter(self.entries))
            del self.entries[oldest]
