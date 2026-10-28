import unittest
from project.core import apply_batch


class AgentBatchTests(unittest.TestCase):
    def test_sequential_versions(self):
        stock, versions = {'A': 5}, {'A': 0}
        changes = [
            {'sku': 'A', 'delta': -2, 'expected_version': 0},
            {'sku': 'A', 'delta': 1, 'expected_version': 1},
        ]
        result = apply_batch(stock, versions, changes)
        self.assertEqual(result, ({'A': 4}, {'A': 2}))
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 0}))
        self.assertEqual(changes[0], {'sku': 'A', 'delta': -2, 'expected_version': 0})

    def test_stale_version_after_first_change(self):
        stock, versions = {'A': 5}, {'A': 0}
        with self.assertRaises(ValueError):
            apply_batch(stock, versions, [
                {'sku': 'A', 'delta': 1, 'expected_version': 0},
                {'sku': 'A', 'delta': 1, 'expected_version': 0},
            ])
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 0}))

    def test_unknown_sku(self):
        with self.assertRaises(KeyError):
            apply_batch({'A': 1}, {'A': 0},
                        [{'sku': 'B', 'delta': 1, 'expected_version': 0}])

    def test_bool_rejected(self):
        for delta, expected in ((True, 0), (1, False), (1, True)):
            with self.assertRaises(ValueError):
                apply_batch({'A': 1}, {'A': 0},
                            [{'sku': 'A', 'delta': delta,
                              'expected_version': expected}])

    def test_negative_expected_version(self):
        with self.assertRaises(ValueError):
            apply_batch({'A': 1}, {'A': 0},
                        [{'sku': 'A', 'delta': 0, 'expected_version': -1}])

    def test_zero_delta_bumps_version(self):
        self.assertEqual(
            apply_batch({'A': 1}, {'A': 3},
                        [{'sku': 'A', 'delta': 0, 'expected_version': 3}]),
            ({'A': 1}, {'A': 4}))

    def test_empty_changes_returns_copies(self):
        stock, versions = {'A': 1}, {'A': 0}
        new_stock, new_versions = apply_batch(stock, versions, [])
        self.assertEqual((new_stock, new_versions), (stock, versions))
        self.assertIsNot(new_stock, stock)
        self.assertIsNot(new_versions, versions)

    def test_missing_key_in_change(self):
        with self.assertRaises(ValueError):
            apply_batch({'A': 1}, {'A': 0}, [{'sku': 'A', 'delta': 1}])


if __name__ == '__main__':
    unittest.main()
