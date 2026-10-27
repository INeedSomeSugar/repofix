import unittest
from project.core import TTLCache


class PublicTests(unittest.TestCase):
    def test_boundary(self):
        cache = TTLCache()
        cache.set("a", 1, ttl=5, now=10)
        self.assertEqual(cache.get("a", now=14), 1)
        self.assertIsNone(cache.get("a", now=15))

    def test_zero_value(self):
        cache = TTLCache()
        cache.set("a", 0, ttl=5, now=10)
        self.assertEqual(cache.get("a", now=11, default=99), 0)
