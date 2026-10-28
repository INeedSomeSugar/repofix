import unittest

from project.core import allocate_cents


class AgentTests(unittest.TestCase):
    def test_public_examples(self):
        self.assertEqual(allocate_cents(10, [1, 1, 1]), [4, 3, 3])
        self.assertEqual(allocate_cents(2, [1, 1, 1]), [1, 1, 0])
        self.assertEqual(allocate_cents(-5, [1, 2]), [-2, -3])

    def test_conservation_and_sign(self):
        for total in (0, 1, 7, -7, 100, -100, 10 ** 30 + 1, -(10 ** 30 + 1)):
            for weights in ([1], [1, 2, 3], [0, 5, 0, 5], [3, 3, 3, 3]):
                result = allocate_cents(total, weights)
                self.assertEqual(sum(result), total)
                self.assertEqual(len(result), len(weights))
                if total < 0:
                    self.assertTrue(all(value <= 0 for value in result))
                else:
                    self.assertTrue(all(value >= 0 for value in result))

    def test_zero_weights_get_zero(self):
        self.assertEqual(allocate_cents(5, [0, 1, 0]), [0, 5, 0])
        self.assertEqual(allocate_cents(-5, [0, 1, 0]), [0, -5, 0])

    def test_tie_break_by_index(self):
        self.assertEqual(allocate_cents(5, [1, 1, 1, 1]), [2, 1, 1, 1])
        self.assertEqual(allocate_cents(-5, [1, 1, 1, 1]), [-2, -1, -1, -1])

    def test_empty(self):
        self.assertEqual(allocate_cents(0, []), [])
        self.assertEqual(allocate_cents(0, ()), [])
        with self.assertRaises(ValueError):
            allocate_cents(1, [])
        with self.assertRaises(ValueError):
            allocate_cents(-1, [])

    def test_invalid_inputs(self):
        for bad_total in (True, False, 1.0, "1", None):
            with self.assertRaises(ValueError):
                allocate_cents(bad_total, [1])
        for bad_weights in ([0, 0], [-1, 2], [True, 1], [1.5, 1], "ab", 5, None):
            with self.assertRaises(ValueError):
                allocate_cents(10, bad_weights)

    def test_input_not_mutated(self):
        weights = [1, 2, 3]
        allocate_cents(10, weights)
        self.assertEqual(weights, [1, 2, 3])

    def test_generator_weights(self):
        self.assertEqual(allocate_cents(10, (w for w in [1, 1, 1])), [4, 3, 3])


if __name__ == "__main__":
    unittest.main()
