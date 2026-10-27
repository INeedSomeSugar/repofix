import unittest
from project.core import split_before, split_after, split_when

class Public(unittest.TestCase):
    def test_empty_zero(self):
        functions = [(split_before, bool), (split_after, bool),
                     (split_when, lambda a, b: a != b)]
        for func, pred in functions:
            with self.subTest(function=func):
                self.assertEqual(list(func(iter([]), pred, maxsplit=0)), [])
    def test_nonempty_zero(self):
        functions = [(split_before, bool), (split_after, bool),
                     (split_when, lambda a, b: True)]
        for func, pred in functions:
            self.assertEqual(list(func(iter([1, 2]), pred, maxsplit=0)), [[1, 2]])
