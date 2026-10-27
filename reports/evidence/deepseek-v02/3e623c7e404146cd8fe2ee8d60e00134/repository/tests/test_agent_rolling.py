import unittest

from project.core import rolling_average


class RollingAverageTests(unittest.TestCase):
    def test_full_windows(self):
        self.assertEqual(rolling_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])
        self.assertEqual(rolling_average([1, 2, 3, 4, 5], 3), [2.0, 3.0, 4.0])

    def test_window_one(self):
        self.assertEqual(rolling_average([2, 5], 1), [2, 5])

    def test_window_equals_length(self):
        self.assertEqual(rolling_average([1, 2, 3], 3), [2.0])

    def test_window_larger_or_empty(self):
        self.assertEqual(rolling_average([1, 2], 3), [])
        self.assertEqual(rolling_average([], 1), [])
        self.assertEqual(rolling_average([], 5), [])

    def test_invalid_window(self):
        for bad in (0, -1, -5, True, False, 1.0, "2", None):
            with self.assertRaises(ValueError):
                rolling_average([1, 2, 3], bad)

    def test_input_not_modified(self):
        data = [1, 2, 3, 4]
        rolling_average(data, 2)
        self.assertEqual(data, [1, 2, 3, 4])

    def test_tuple_input(self):
        self.assertEqual(rolling_average((1, 2, 3), 2), [1.5, 2.5])


if __name__ == "__main__":
    unittest.main()
