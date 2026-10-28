import unittest

from project.core import allocate_cents


class AgentAllocateTests(unittest.TestCase):
    def test_public_examples(self):
        self.assertEqual(allocate_cents(10, [1, 1, 1]), [4, 3, 3])
        self.assertEqual(allocate_cents(2, [1, 1, 1]), [1, 1, 0])
        self.assertEqual(allocate_cents(-5, [1, 2]), [-2, -3])

    def test_conservation_and_sign(self):
        for total in (-1000, -7, -1, 0, 1, 7, 1000, 10 ** 30 + 1):
            for weights in ([1], [1, 2, 3], [0, 5, 0], [3, 3, 3, 3], [7, 1, 2, 9]):
                result = allocate_cents(total, weights)
                self.assertEqual(sum(result), total)
                self.assertEqual(len(result), len(weights))
                if total < 0:
                    self.assertTrue(all(value <= 0 for value in result))
                else:
                    self.assertTrue(all(value >= 0 for value in result))

    def test_tie_break_by_index(self):
        self.assertEqual(allocate_cents(5, [1, 1, 1, 1]), [2, 1, 1, 1])
        self.assertEqual(allocate_cents(-5, [1, 1, 1, 1]), [-2, -1, -1, -1])

    def test_zero_weights(self):
        self.assertEqual(allocate_cents(5, [0, 1, 0]), [0, 5, 0])
        with self.assertRaises(ValueError):
            allocate_cents(0, [0, 0])

    def test_iterables_and_no_mutation(self):
        weights = (1, 2, 3)
        self.assertEqual(allocate_cents(6, weights), [1, 2, 3])
        self.assertEqual(weights, (1, 2, 3))
        self.assertEqual(allocate_cents(6, iter([1, 2, 3])), [1, 2, 3])

    def test_empty(self):
        self.assertEqual(allocate_cents(0, []), [])
        with self.assertRaises(ValueError):
            allocate_cents(1, [])
        with self.assertRaises(ValueError):
            allocate_cents(-1, [])

    def test_invalid_inputs(self):
        for bad_total in (True, False, 1.0, "1", None):
            with self.assertRaises(ValueError):
                allocate_cents(bad_total, [1])
        for bad_weights in ([True], [1, False], [-1, 2], [1.5], ["1"], None, 5, "ab"):
            with self.assertRaises(ValueError):
                allocate_cents(5, bad_weights)
        with self.assertRaises(ValueError):
            allocate_cents(5, [0, 0])
        with self.assertRaises(ValueError):
            allocate_cents(0, [0])

    def test_large_exact(self):
        big = 10 ** 40 + 3
        result = allocate_cents(big, [1, 1, 1])
        self.assertEqual(sum(result), big)
        self.assertEqual(result[0] - result[2], 1)


if __name__ == "__main__":
    unittest.main()
