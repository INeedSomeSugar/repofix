import unittest
from project.core import merge_intervals


class PublicTests(unittest.TestCase):
    def test_overlapping(self):
        self.assertEqual(merge_intervals([[1, 4], [2, 5], [8, 9]]), [[1, 5], [8, 9]])

    def test_touching(self):
        self.assertEqual(merge_intervals([[1, 2], [2, 3]]), [[1, 3]])
