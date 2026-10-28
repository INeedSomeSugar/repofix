import unittest
from project.core import apply_batch
class PublicTests(unittest.TestCase):
    def test_success_does_not_mutate(self):
        stock, versions = {'A': 5}, {'A': 2}
        result = apply_batch(stock, versions,
                             [{'sku': 'A', 'delta': -2, 'expected_version': 2}])
        self.assertEqual(result, ({'A': 3}, {'A': 3}))
        self.assertEqual((stock, versions), ({'A': 5}, {'A': 2}))
    def test_failure_is_atomic(self):
        stock, versions = {'A': 5}, {'A': 0}
        with self.assertRaises(ValueError):
            apply_batch(stock, versions,
                        [{'sku': 'A', 'delta': -8, 'expected_version': 0}])
        self.assertEqual(stock, {'A': 5})
