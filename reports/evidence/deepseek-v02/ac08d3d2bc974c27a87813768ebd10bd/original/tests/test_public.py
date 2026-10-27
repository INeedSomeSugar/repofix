import unittest
from project.core import rolling_average


class PublicTests(unittest.TestCase):
    def test_full_windows(self):
        self.assertEqual(rolling_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])

    def test_window_one(self):
        self.assertEqual(rolling_average([2, 5], 1), [2, 5])
