import unittest

from project.core import page


class AgentPageTests(unittest.TestCase):
    def test_limit_validation(self):
        for bad in (0, -1, 101, True, False, 1.0, '3', None):
            with self.assertRaises(ValueError):
                page([], bad)
        for good in (1, 100):
            self.assertEqual(page([], good), {'items': [], 'next_cursor': None})

    def test_empty_and_no_records_after_cursor(self):
        self.assertEqual(page([], 5), {'items': [], 'next_cursor': None})
        rows = [{'sequence': 1, 'event_id': 'a'}]
        self.assertEqual(page(rows, 5, [1, 'a']),
                         {'items': [], 'next_cursor': None})
        self.assertEqual(page(rows, 5, [2, 'a']),
                         {'items': [], 'next_cursor': None})

    def test_cursor_not_existing(self):
        rows = [{'sequence': 1, 'event_id': 'a'},
                {'sequence': 2, 'event_id': 'b'},
                {'sequence': 2, 'event_id': 'c'}]
        result = page(rows, 10, [1, 'z'])
        self.assertEqual([r['event_id'] for r in result['items']], ['b', 'c'])
        self.assertIsNone(result['next_cursor'])
        result = page(rows, 10, [2, 'b'])
        self.assertEqual([r['event_id'] for r in result['items']], ['c'])

    def test_no_mutation_and_shallow_copy(self):
        rows = [{'sequence': 2, 'event_id': 'c'},
                {'sequence': 1, 'event_id': 'b'},
                {'sequence': 1, 'event_id': 'a'}]
        snapshot = [dict(r) for r in rows]
        result = page(rows, 2)
        self.assertEqual(rows, snapshot)
        self.assertEqual([r['event_id'] for r in result['items']], ['a', 'b'])
        self.assertEqual(result['next_cursor'], [1, 'b'])
        self.assertIsNot(result['items'][0], rows[2])
        self.assertEqual(result['items'][0], rows[2])

    def test_iterable_input(self):
        rows = ({'sequence': i, 'event_id': 'e%d' % i} for i in range(3))
        result = page(rows, 2)
        self.assertEqual([r['sequence'] for r in result['items']], [0, 1])
        self.assertEqual(result['next_cursor'], [1, 'e1'])

    def test_exact_page_has_no_cursor(self):
        rows = [{'sequence': 1, 'event_id': 'a'},
                {'sequence': 2, 'event_id': 'b'}]
        result = page(rows, 2)
        self.assertEqual(len(result['items']), 2)
        self.assertIsNone(result['next_cursor'])


if __name__ == '__main__':
    unittest.main()
