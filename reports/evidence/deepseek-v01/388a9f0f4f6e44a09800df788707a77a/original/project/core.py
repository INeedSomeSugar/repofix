def parse_records(text):
    lines = text.strip().splitlines()
    if not lines:
        return []
    headers = [value.strip() for value in lines[0].split(",")]
    return [dict(zip(headers, [v.strip() for v in line.split(",")]))
            for line in lines[1:]]
