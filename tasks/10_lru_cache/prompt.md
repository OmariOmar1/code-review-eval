# LRU Cache

Write a class `LRUCache`.

- `LRUCache(capacity)` creates a cache holding at most `capacity` entries.
  Raise `ValueError` if `capacity` is less than 1.
- `get(key)` returns the stored value, or `None` if the key is absent. A
  successful `get` marks the key as most recently used.
- `put(key, value)` inserts or updates an entry and marks it as most recently
  used. When the cache is over capacity, the least recently used entry is
  evicted.
- `len(cache)` returns the number of stored entries.
