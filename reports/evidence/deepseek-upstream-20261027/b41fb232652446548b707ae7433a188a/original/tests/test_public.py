import unittest
from project.core import value_chain

class Public(unittest.TestCase):
    def test_mixed(self):
        actual = list(value_chain(1, [2, 3], 'ab', b'cd'))
        self.assertEqual(actual, [1, 2, 3, 'ab', b'cd'])
    def test_error_during_consumption(self):
        result = value_chain(map(len, ['ab', 7]))
        self.assertEqual(next(result), 2)
        with self.assertRaises(TypeError):
            next(result)
