import unittest
from project.core import top_words


class TopWordsTests(unittest.TestCase):
    def test_case_insensitive_and_ascii_only(self):
        self.assertEqual(
            top_words("Hello hello HELLO world, world! \u00e9t\u00e9 123", 2),
            [("hello", 3), ("world", 2)],
        )

    def test_tie_lexicographic(self):
        self.assertEqual(
            top_words("b a c b a c", 3), [("a", 2), ("b", 2), ("c", 2)]
        )

    def test_k_zero_and_no_words(self):
        self.assertEqual(top_words("a b", 0), [])
        self.assertEqual(top_words("", 5), [])
        self.assertEqual(top_words("123 !!!", 5), [])

    def test_k_larger_than_distinct(self):
        self.assertEqual(top_words("a a b", 10), [("a", 2), ("b", 1)])

    def test_invalid_k(self):
        for bad in (-1, True, False, 1.0, "1", None):
            with self.assertRaises(ValueError):
                top_words("a b", bad)


if __name__ == "__main__":
    unittest.main()
