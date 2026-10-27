import unittest

from project.core import rolling_average


class RollingAverageTests(unittest.TestCase):
    def test_full_windows(self):
        self.assertEqual(rolling_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])

    def test_window_one(self):
        self.assertEqual(rolling_average([2, 5], 1), [2, 5])

    def test_window_equals_length(self):
        self.assertEqual(rolling_average([1, 2, 3], 3), [2.0])

    def test_window_larger_than_input(self):
        self.assertEqual(rolling_average([1, 2], 5), [])

    def test_empty_input(self):
        self.assertEqual(rolling_average([], 1), [])

    def test_invalid_window(self):
        for bad in (0, -1, 1.0, "2", None, True, False):
            with self.assertRaises(ValueError):
                rolling_average([1, 2, 3], bad)

    def test_input_not_modified(self):
        values = [1, 2, 3, 4]
        rolling_average(values, 2)
        self.assertEqual(values, [1, 2, 3, 4])

    def test_tuple_input(self):
        self.assertEqual(rolling_average((1, 2, 3, 4), 3), [2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
