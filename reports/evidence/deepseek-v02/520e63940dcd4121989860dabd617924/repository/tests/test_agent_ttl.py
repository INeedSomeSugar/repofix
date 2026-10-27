import unittest
from project.core import TTLCache


class TTLCacheTests(unittest.TestCase):
    def test_boundary_expiry(self):
        cache = TTLCache()
        cache.set("a", 1, ttl=5, now=10)
        self.assertEqual(cache.get("a", now=14), 1)
        self.assertIsNone(cache.get("a", now=15))
        self.assertIsNone(cache.get("a", now=16))

    def test_falsy_values_preserved(self):
        cache = TTLCache()
        for i, value in enumerate([0, False, "", None]):
            cache.set(i, value, ttl=5, now=10)
            self.assertEqual(cache.get(i, now=11, default=99), value)
            self.assertIs(cache.get(i, now=11, default=99), value)

    def test_negative_ttl_raises(self):
        cache = TTLCache()
        with self.assertRaises(ValueError):
            cache.set("a", 1, ttl=-1, now=10)
        self.assertIsNone(cache.get("a", now=10))

    def test_zero_ttl_expires_immediately(self):
        cache = TTLCache()
        cache.set("a", 1, ttl=0, now=10)
        self.assertIsNone(cache.get("a", now=10))

    def test_reset_overwrites(self):
        cache = TTLCache()
        cache.set("a", 1, ttl=5, now=10)
        cache.set("a", 2, ttl=100, now=12)
        self.assertEqual(cache.get("a", now=20), 2)
        cache.set("a", 3, ttl=1, now=20)
        self.assertIsNone(cache.get("a", now=21))
        self.assertEqual(cache.get("a", now=20, default="d"), "d")

    def test_missing_key_default(self):
        cache = TTLCache()
        self.assertIsNone(cache.get("x", now=0))
        self.assertEqual(cache.get("x", now=0, default=7), 7)


if __name__ == "__main__":
    unittest.main()
