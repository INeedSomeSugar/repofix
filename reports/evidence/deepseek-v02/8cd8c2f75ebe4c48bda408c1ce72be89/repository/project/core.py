import csv
import io


def _is_blank_row(fields):
    return all(field.strip() == "" for field in fields)


def parse_records(text):
    """Parse CSV text into a list of dicts keyed by the header row.

    The first non-blank line is the header. Blank lines and rows whose
    fields are all whitespace are skipped. Standard CSV quoting (including
    commas inside quoted fields) is supported, and each field is stripped
    of surrounding whitespace. Returns [] for empty input or header-only
    input. Raises ValueError when a non-blank data row has a field count
    different from the header. The input string is never modified.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        return []

    reader = csv.reader(io.StringIO(text, newline=""))
    headers = None
    records = []
    for row in reader:
        if _is_blank_row(row):
            continue
        fields = [field.strip() for field in row]
        if headers is None:
            headers = fields
            continue
        if len(fields) != len(headers):
            raise ValueError(
                "row has %d fields, expected %d" % (len(fields), len(headers))
            )
        records.append(dict(zip(headers, fields)))
    return records
