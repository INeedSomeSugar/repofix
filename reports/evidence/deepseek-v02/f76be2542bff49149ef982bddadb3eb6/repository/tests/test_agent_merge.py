import unittest

from project.core import merge_intervals
from project.utils import overlaps


class MergeIntervalsTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])

    def test_overlaps_helper(self):
        self.assertTrue(overlaps([1, 2], [2, 3]))
        self.assertTrue(overlaps([1, 5], [2, 3]))
        self.assertFalse(overlaps([1, 2], [3, 4]))

    def test_unsorted_input_and_nesting(self):
        self.assertEqual(
            merge_intervals([[8, 10], [1, 5], [2, 3], [4, 6], [10, 12]]),
            [[1, 6], [8, 12]],
        )

    def test_does_not_mutate_or_reuse_input(self):
        data = [[3, 4], [1, 2], [2, 3]]
        snapshot = [list(item) for item in data]
        result = merge_intervals(data)
        self.assertEqual(data, snapshot)
        self.assertEqual(result, [[1, 4]])
        for out in result:
            self.assertFalse(any(out is item for item in data))

    def test_single_and_duplicates(self):
        self.assertEqual(merge_intervals([[5, 5]]), [[5, 5]])
        self.assertEqual(merge_intervals([[1, 2], [1, 2]]), [[1, 2]])


if __name__ == "__main__":
    unittest.main()
