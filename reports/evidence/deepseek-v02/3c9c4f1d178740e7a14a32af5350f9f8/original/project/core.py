class TTLCache:
    def __init__(self):
        self._items = {}

    def set(self, key, value, ttl, now):
        self._items[key] = (value, now + ttl)

    def get(self, key, now, default=None):
        if key not in self._items:
            return default
        value, expires = self._items[key]
        if now > expires:
            del self._items[key]
            return default
        return value or default
