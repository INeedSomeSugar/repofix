import unittest
from project.core import allocate_cents
class PublicTests(unittest.TestCase):
    def test_conservation_and_ties(self):
        self.assertEqual(allocate_cents(10, [1, 1, 1]), [4, 3, 3])
        self.assertEqual(allocate_cents(2, [1, 1, 1]), [1, 1, 0])
    def test_negative(self):
        self.assertEqual(allocate_cents(-5, [1, 2]), [-2, -3])
