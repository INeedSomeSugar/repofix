import unittest

from project.core import merge_intervals
from project.utils import overlaps


class MergeIntervalsTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])

    def test_touching_and_overlapping(self):
        self.assertEqual(merge_intervals([[1, 2], [2, 3]]), [[1, 3]])
        self.assertEqual(merge_intervals([[1, 4], [2, 5], [8, 9]]), [[1, 5], [8, 9]])

    def test_unsorted_and_nested(self):
        self.assertEqual(
            merge_intervals([[8, 10], [1, 5], [2, 3], [5, 6], [20, 21]]),
            [[1, 6], [8, 10], [20, 21]],
        )

    def test_single_point_intervals(self):
        self.assertEqual(merge_intervals([[3, 3], [3, 4], [5, 5]]), [[3, 4], [5, 5]])

    def test_input_not_mutated_or_reused(self):
        data = [[5, 7], [1, 3], [3, 4]]
        snapshot = [list(item) for item in data]
        result = merge_intervals(data)
        self.assertEqual(data, snapshot)
        self.assertEqual(result, [[1, 4], [5, 7]])
        for out in result:
            self.assertFalse(any(out is item for item in data))
        result[0][0] = -100
        self.assertEqual(data, snapshot)

    def test_overlaps_helper(self):
        self.assertTrue(overlaps([1, 2], [2, 3]))
        self.assertTrue(overlaps([1, 5], [2, 3]))
        self.assertFalse(overlaps([1, 2], [3, 4]))


if __name__ == "__main__":
    unittest.main()
