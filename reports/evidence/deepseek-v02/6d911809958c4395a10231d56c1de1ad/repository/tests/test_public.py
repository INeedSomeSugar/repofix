import unittest
from project.core import parse_records


class PublicTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(parse_records("name,age\nAmy,20"), [{"name": "Amy", "age": "20"}])

    def test_blank_rows(self):
        self.assertEqual(parse_records("name,age\nAmy,20\n\nBob,21"),
                         [{"name": "Amy", "age": "20"}, {"name": "Bob", "age": "21"}])
