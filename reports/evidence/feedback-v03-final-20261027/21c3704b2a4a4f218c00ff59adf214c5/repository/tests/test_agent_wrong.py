import unittest
from project.core import rolling_average
class GeneratedHypothesis(unittest.TestCase):
    def test_wrong_expectation(self):
        self.assertEqual(rolling_average([1, 2, 3], 2), [])
