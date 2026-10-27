import unittest

from project.core import top_words


class TopWordsTests(unittest.TestCase):
    def test_case_insensitive_and_ascii_only(self):
        self.assertEqual(
            top_words("Hello hello HELLO world", 2),
            [("hello", 3), ("world", 1)],
        )

    def test_non_ascii_letters_are_separators(self):
        self.assertEqual(top_words("caf\u00e9 cat", 2), [("caf", 1), ("cat", 1)])

    def test_tie_lexicographic(self):
        self.assertEqual(
            top_words("b a c b a", 3),
            [("a", 2), ("b", 2), ("c", 1)],
        )

    def test_k_zero_and_no_words(self):
        self.assertEqual(top_words("a b", 0), [])
        self.assertEqual(top_words("123 !!!", 5), [])
        self.assertEqual(top_words("", 3), [])

    def test_k_larger_than_distinct(self):
        self.assertEqual(top_words("a a b", 10), [("a", 2), ("b", 1)])

    def test_invalid_k(self):
        for bad in (-1, True, False, 1.0, "2", None):
            with self.assertRaises(ValueError):
                top_words("a b", bad)


if __name__ == "__main__":
    unittest.main()
