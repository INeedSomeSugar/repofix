import unittest

from project.core import parse_records


class AgentCsvTests(unittest.TestCase):
    def test_empty_and_header_only(self):
        self.assertEqual(parse_records(""), [])
        self.assertEqual(parse_records("   \n\n"), [])
        self.assertEqual(parse_records("name,age"), [])
        self.assertEqual(parse_records("name,age\n\n  \n"), [])

    def test_leading_blank_lines_before_header(self):
        self.assertEqual(parse_records("\n\nname,age\nAmy,20"),
                         [{"name": "Amy", "age": "20"}])

    def test_whitespace_only_rows_skipped(self):
        self.assertEqual(parse_records("name,age\n , \nAmy,20\n\t,\n"),
                         [{"name": "Amy", "age": "20"}])

    def test_quoted_fields_and_commas(self):
        text = 'name,note\n"Smith, John","say ""hi"""\n'
        self.assertEqual(parse_records(text),
                         [{"name": "Smith, John", "note": 'say "hi"'}])

    def test_quoted_multiline_field(self):
        text = 'name,note\nAmy,"line1\nline2"\n'
        self.assertEqual(parse_records(text),
                         [{"name": "Amy", "note": "line1\nline2"}])

    def test_field_whitespace_stripped(self):
        self.assertEqual(parse_records(" name , age \n  Amy  , 20 "),
                         [{"name": "Amy", "age": "20"}])

    def test_mismatched_field_count_raises(self):
        with self.assertRaises(ValueError):
            parse_records("name,age\nAmy,20,extra")
        with self.assertRaises(ValueError):
            parse_records("name,age\nAmy")

    def test_input_not_modified(self):
        text = "name,age\nAmy,20\n"
        original = text
        parse_records(text)
        self.assertEqual(text, original)


if __name__ == "__main__":
    unittest.main()
