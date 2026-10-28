import unittest
from project.core import page
class PublicTests(unittest.TestCase):
    def test_same_sequence_and_terminal_cursor(self):
        rows = [{'sequence': 2, 'event_id': 'c'}, {'sequence': 1, 'event_id': 'b'},
                {'sequence': 1, 'event_id': 'a'}]
        first = page(rows, 1)
        self.assertEqual(first['next_cursor'], [1, 'a'])
        last = page(rows, 2, [1, 'a'])
        self.assertEqual([r['event_id'] for r in last['items']], ['b', 'c'])
        self.assertIsNone(last['next_cursor'])
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            page([], 0)
