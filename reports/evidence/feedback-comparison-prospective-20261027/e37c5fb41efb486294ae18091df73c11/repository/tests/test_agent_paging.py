import unittest
from project.core import page


class AgentPagingTests(unittest.TestCase):
    def rows(self):
        return [
            {'sequence': 2, 'event_id': 'c'},
            {'sequence': 1, 'event_id': 'b'},
            {'sequence': 1, 'event_id': 'a'},
            {'sequence': 3, 'event_id': 'a'},
        ]

    def test_order_and_copies(self):
        rows = self.rows()
        snapshot = [dict(r) for r in rows]
        result = page(rows, 2)
        self.assertEqual([(r['sequence'], r['event_id']) for r in result['items']],
                         [(1, 'a'), (1, 'b')])
        self.assertEqual(result['next_cursor'], [1, 'b'])
        self.assertEqual(rows, snapshot)
        result['items'][0]['sequence'] = 99
        self.assertEqual(rows, snapshot)

    def test_cursor_not_existing(self):
        rows = self.rows()
        result = page(rows, 10, [1, 'aa'])
        self.assertEqual([r['event_id'] for r in result['items']], ['b', 'c', 'a'])
        self.assertIsNone(result['next_cursor'])

    def test_empty_and_beyond(self):
        self.assertEqual(page([], 5), {'items': [], 'next_cursor': None})
        self.assertEqual(page(self.rows(), 5, [9, 'z']),
                         {'items': [], 'next_cursor': None})

    def test_invalid_limits(self):
        for bad in (0, 101, -1, True, False, 1.0, '3', None):
            with self.assertRaises(ValueError):
                page([], bad)

    def test_valid_limits(self):
        self.assertEqual(page([], 1)['items'], [])
        self.assertEqual(page([], 100)['items'], [])

    def test_iterable_input(self):
        gen = (r for r in self.rows())
        result = page(gen, 1)
        self.assertEqual(result['next_cursor'], [1, 'a'])


if __name__ == '__main__':
    unittest.main()
