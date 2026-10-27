import unittest
from project.core import split_before, split_after, split_when


class SplitZero(unittest.TestCase):
    def test_empty_zero(self):
        for func, pred in [(split_before, bool), (split_after, bool),
                           (split_when, lambda a, b: a != b)]:
            with self.subTest(function=func):
                self.assertEqual(list(func(iter([]), pred, maxsplit=0)), [])

    def test_nonempty_zero(self):
        for func, pred in [(split_before, bool), (split_after, bool),
                           (split_when, lambda a, b: True)]:
            with self.subTest(function=func):
                self.assertEqual(list(func(iter([1, 2, 3]), pred, maxsplit=0)),
                                 [[1, 2, 3]])

    def test_zero_is_lazy(self):
        def gen():
            raise AssertionError("should not be consumed eagerly")
            yield 1
        for func, pred in [(split_before, bool), (split_after, bool),
                           (split_when, lambda a, b: True)]:
            with self.subTest(function=func):
                it = func(gen(), pred, maxsplit=0)
                self.assertTrue(hasattr(it, "next") or hasattr(it, "__next__"))

    def test_other_maxsplit_unchanged(self):
        self.assertEqual(list(split_before(range(10), lambda n: n % 3 == 0, maxsplit=2)),
                         [[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]])
        self.assertEqual(list(split_after(range(10), lambda n: n % 3 == 0, maxsplit=2)),
                         [[0], [1, 2, 3], [4, 5, 6, 7, 8, 9]])
        self.assertEqual(list(split_when([1, 2, 3, 3, 2, 5, 2, 4, 2],
                                         lambda x, y: x > y, maxsplit=2)),
                         [[1, 2, 3, 3], [2, 5], [2, 4, 2]])
        self.assertEqual(list(split_before('OneTwo', lambda s: s.isupper())),
                         [['O', 'n', 'e'], ['T', 'w', 'o']])
        self.assertEqual(list(split_after('one1two2', lambda s: s.isdigit())),
                         [['o', 'n', 'e', '1'], ['t', 'w', 'o', '2']])
        self.assertEqual(list(split_when([1, 2, 3, 3, 2, 5, 2, 4, 2],
                                         lambda x, y: x > y)),
                         [[1, 2, 3, 3], [2, 5], [2, 4], [2]])


if __name__ == "__main__":
    unittest.main()
