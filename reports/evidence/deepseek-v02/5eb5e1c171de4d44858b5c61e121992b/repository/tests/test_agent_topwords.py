import unittest

from project.core import top_words


class TopWordsTests(unittest.TestCase):
    def test_case_insensitive_and_punctuation(self):
        self.assertEqual(
            top_words("Hello, hello! WORLD-world 123", 2),
            [("hello", 2), ("world", 2)],
        )

    def test_tie_lexicographic(self):
        self.assertEqual(
            top_words("b a c a b c d", 4),
            [("a", 2), ("b", 2), ("c", 2), ("d", 1)],
        )

    def test_k_zero_and_no_words(self):
        self.assertEqual(top_words("abc", 0), [])
        self.assertEqual(top_words("123 !!!", 5), [])
        self.assertEqual(top_words("", 3), [])

    def test_k_larger_than_distinct(self):
        self.assertEqual(top_words("x y x", 10), [("x", 2), ("y", 1)])

    def test_invalid_k(self):
        for bad in (-1, True, False, 1.0, "2", None):
            with self.assertRaises(ValueError):
                top_words("a b", bad)


if __name__ == "__main__":
    unittest.main()
