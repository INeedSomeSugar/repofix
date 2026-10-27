import unittest
from project.core import top_words


class PublicTests(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(top_words("cat dog cat", 1), [("cat", 2)])

    def test_tie(self):
        self.assertEqual(top_words("dog cat", 2), [("cat", 1), ("dog", 1)])
