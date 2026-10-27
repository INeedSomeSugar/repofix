import unittest
from project.core import one, only

class FalsyError(Exception):
    def __bool__(self):
        return False

class Public(unittest.TestCase):
    def test_custom_long(self):
        for func in [one, only]:
            with self.assertRaises(FalsyError):
                func([1, 2], too_long=FalsyError('many'))
    def test_custom_short(self):
        with self.assertRaises(FalsyError):
            one([], too_short=FalsyError('few'))
    def test_single(self):
        self.assertEqual(one([7]), 7)
        self.assertEqual(only([7]), 7)
