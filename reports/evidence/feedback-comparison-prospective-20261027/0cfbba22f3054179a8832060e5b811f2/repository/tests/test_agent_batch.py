import unittest

from project.core import apply_batch


class AgentBatchTests(unittest.TestCase):
    def test_sequential_versions(self):
        stock, versions = {'A': 5}, {'A': 0}
        changes = [
            {'sku': 'A', 'delta': -2, 'expected_version': 0},
            {'sku': 'A', 'delta': 0, 'expected_version': 1},
        ]
        new_stock, new_versions = apply_batch(stock, versions, changes)
        self.assertEqual((new_stock, new_versions), ({'A': 3}, {'A': 2}))
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 0}))
        self.assertIsNot(new_stock, stock)
        self.assertIsNot(new_versions, versions)

    def test_stale_version_after_first_change(self):
        stock, versions = {'A': 5}, {'A': 0}
        with self.assertRaises(ValueError):
            apply_batch(stock, versions, [
                {'sku': 'A', 'delta': -1, 'expected_version': 0},
                {'sku': 'A', 'delta': -1, 'expected_version': 0},
            ])
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 0}))

    def test_bool_rejected(self):
        stock, versions = {'A': 5}, {'A': 0}
        for delta, expected in ((True, 0), (1, False), (1, True)):
            with self.assertRaises(ValueError):
                apply_batch(stock, versions,
                            [{'sku': 'A', 'delta': delta,
                              'expected_version': expected}])
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 0}))

    def test_unknown_sku(self):
        with self.assertRaises(KeyError):
            apply_batch({'A': 1}, {'A': 0},
                        [{'sku': 'B', 'delta': 1, 'expected_version': 0}])

    def test_empty_changes_returns_copies(self):
        stock, versions = {'A': 1}, {'A': 0}
        new_stock, new_versions = apply_batch(stock, versions, [])
        self.assertEqual((new_stock, new_versions), (stock, versions))
        self.assertIsNot(new_stock, stock)
        self.assertIsNot(new_versions, versions)

    def test_changes_not_mutated(self):
        change = {'sku': 'A', 'delta': 2, 'expected_version': 0}
        apply_batch({'A': 1}, {'A': 0}, [change])
        self.assertEqual(change, {'sku': 'A', 'delta': 2, 'expected_version': 0})


if __name__ == '__main__':
    unittest.main()
