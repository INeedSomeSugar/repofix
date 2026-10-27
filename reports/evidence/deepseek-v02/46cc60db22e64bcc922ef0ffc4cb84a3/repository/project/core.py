import csv
import io


def _is_blank_row(row):
    return all(not field.strip() for field in row)


def parse_records(text):
    """Parse CSV text into a list of dicts keyed by the header row.

    The first non-blank line is the header. Blank lines and rows whose
    fields are all whitespace are skipped. Standard CSV quoting (including
    commas inside quoted fields) is supported, and each field is stripped
    of surrounding whitespace. A non-blank data row whose field count does
    not match the header raises ValueError. The input string is not
    modified.
    """
    if text is None:
        return []
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    reader = csv.reader(io.StringIO(text, newline=""))

    headers = None
    records = []
    for row in reader:
        if not row or _is_blank_row(row):
            continue
        if headers is None:
            headers = [field.strip() for field in row]
            continue
        if len(row) != len(headers):
            raise ValueError(
                "row has %d fields but header has %d" % (len(row), len(headers))
            )
        records.append(
            {header: field.strip() for header, field in zip(headers, row)}
        )
    return records
