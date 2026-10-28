import unittest
from project.core import page


class PageTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {'sequence': 2, 'event_id': 'c'},
            {'sequence': 1, 'event_id': 'b'},
            {'sequence': 1, 'event_id': 'a'},
            {'sequence': 3, 'event_id': 'a'},
        ]

    def test_order_and_cursor(self):
        result = page(self.rows, 2)
        self.assertEqual([r['event_id'] for r in result['items']], ['a', 'b'])
        self.assertEqual(result['next_cursor'], [1, 'b'])
        nxt = page(self.rows, 2, result['next_cursor'])
        self.assertEqual([(r['sequence'], r['event_id']) for r in nxt['items']],
                         [(2, 'c'), (3, 'a')])
        self.assertIsNone(nxt['next_cursor'])

    def test_cursor_not_existing(self):
        result = page(self.rows, 10, [1, 'aa'])
        self.assertEqual([(r['sequence'], r['event_id']) for r in result['items']],
                         [(1, 'b'), (2, 'c'), (3, 'a')])
        self.assertIsNone(result['next_cursor'])

    def test_empty_and_beyond(self):
        self.assertEqual(page([], 5), {'items': [], 'next_cursor': None})
        self.assertEqual(page(self.rows, 5, [9, 'z']),
                         {'items': [], 'next_cursor': None})

    def test_invalid_limits(self):
        for bad in (0, 101, -1, True, False, 1.0, '3', None):
            with self.assertRaises(ValueError):
                page(self.rows, bad)
        self.assertEqual(len(page(self.rows, 100)['items']), 4)

    def test_no_mutation_and_shallow_copy(self):
        snapshot = [dict(r) for r in self.rows]
        order = list(self.rows)
        result = page(self.rows, 3)
        self.assertEqual(self.rows, snapshot)
        self.assertEqual([id(r) for r in self.rows], [id(r) for r in order])
        originals = {(r['sequence'], r['event_id']): r for r in self.rows}
        for item in result['items']:
            original = originals[(item['sequence'], item['event_id'])]
            self.assertIsNot(item, original)
            self.assertEqual(item, original)

    def test_iterable_input(self):
        result = page(iter(self.rows), 1)
        self.assertEqual(result['items'], [{'sequence': 1, 'event_id': 'a'}])
        self.assertEqual(result['next_cursor'], [1, 'a'])


if __name__ == '__main__':
    unittest.main()
