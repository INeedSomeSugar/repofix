import unittest

from project.core import allocate_cents


class AgentAllocateTests(unittest.TestCase):
    def test_public_examples(self):
        self.assertEqual(allocate_cents(10, [1, 1, 1]), [4, 3, 3])
        self.assertEqual(allocate_cents(2, [1, 1, 1]), [1, 1, 0])
        self.assertEqual(allocate_cents(-5, [1, 2]), [-2, -3])

    def test_conservation_and_sign(self):
        for total in (-100, -7, -1, 0, 1, 7, 100):
            for weights in ([1], [1, 2], [3, 0, 4], [5, 5, 5, 5], [0, 0, 1]):
                result = allocate_cents(total, weights)
                self.assertEqual(sum(result), total)
                self.assertEqual(len(result), len(weights))
                if total < 0:
                    self.assertTrue(all(v <= 0 for v in result))
                else:
                    self.assertTrue(all(v >= 0 for v in result))

    def test_tie_break_by_index(self):
        self.assertEqual(allocate_cents(5, [1, 1, 1, 1]), [2, 1, 1, 1])
        self.assertEqual(allocate_cents(-5, [1, 1, 1, 1]), [-2, -1, -1, -1])

    def test_zero_weights(self):
        self.assertEqual(allocate_cents(5, [0, 1, 0]), [0, 5, 0])
        with self.assertRaises(ValueError):
            allocate_cents(0, [0, 0])

    def test_empty(self):
        self.assertEqual(allocate_cents(0, []), [])
        self.assertEqual(allocate_cents(0, iter([])), [])
        with self.assertRaises(ValueError):
            allocate_cents(1, [])
        with self.assertRaises(ValueError):
            allocate_cents(-1, [])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            allocate_cents(True, [1])
        with self.assertRaises(ValueError):
            allocate_cents(1.0, [1])
        with self.assertRaises(ValueError):
            allocate_cents("1", [1])
        with self.assertRaises(ValueError):
            allocate_cents(1, [True])
        with self.assertRaises(ValueError):
            allocate_cents(1, [1.5])
        with self.assertRaises(ValueError):
            allocate_cents(1, [-1, 2])
        with self.assertRaises(ValueError):
            allocate_cents(1, [0, 0])
        with self.assertRaises(ValueError):
            allocate_cents(1, 5)
        with self.assertRaises(ValueError):
            allocate_cents(1, "ab")

    def test_no_mutation_and_iterables(self):
        weights = [1, 2, 3]
        allocate_cents(10, weights)
        self.assertEqual(weights, [1, 2, 3])
        self.assertEqual(allocate_cents(10, (1, 2, 3)), allocate_cents(10, [1, 2, 3]))
        self.assertEqual(allocate_cents(10, iter([1, 2, 3])), allocate_cents(10, [1, 2, 3]))

    def test_large_integers_exact(self):
        big = 10 ** 30 + 7
        result = allocate_cents(big, [1, 1, 1])
        self.assertEqual(sum(result), big)
        base = big // 3
        self.assertEqual(result[0], base + 1)
        self.assertEqual(result[1], base + 1)
        self.assertEqual(result[2], base)
        negative = allocate_cents(-big, [1, 1, 1])
        self.assertEqual(negative, [-value for value in result])


if __name__ == "__main__":
    unittest.main()
