import unittest

from project.core import one, only


class FalsyError(Exception):
    def __bool__(self):
        return False


class BadRepr:
    def __repr__(self):
        raise RuntimeError('repr should not be called')


class AgentTests(unittest.TestCase):
    def test_falsy_custom_exceptions_raised(self):
        for func in (one, only):
            with self.assertRaises(FalsyError):
                func([1, 2], too_long=FalsyError('many'))
        with self.assertRaises(FalsyError):
            one([], too_short=FalsyError('few'))

    def test_custom_too_long_skips_repr(self):
        for func in (one, only):
            with self.assertRaises(FalsyError):
                func([BadRepr(), BadRepr()], too_long=FalsyError('many'))

    def test_default_messages(self):
        with self.assertRaises(ValueError) as ctx:
            one([])
        self.assertIn('too few items', str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            only([1, 2])
        self.assertIn('Expected exactly one item', str(ctx.exception))

    def test_single_and_default(self):
        self.assertEqual(one([7]), 7)
        self.assertEqual(only([7]), 7)
        self.assertEqual(only([], default='missing'), 'missing')
        self.assertIsNone(only([]))
        self.assertEqual(one(iter([7])), 7)


if __name__ == '__main__':
    unittest.main()
