def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer between 1 and 100')
    if limit < 1 or limit > 100:
        raise ValueError('limit must be an integer between 1 and 100')


def _normalize_cursor(after):
    if after is None:
        return None
    try:
        parts = list(after)
    except TypeError:
        raise ValueError('after must be a two-element sequence')
    if len(parts) != 2:
        raise ValueError('after must be a two-element sequence')
    sequence, event_id = parts
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise ValueError('after sequence must be an integer')
    if not isinstance(event_id, str):
        raise ValueError('after event_id must be a string')
    return (sequence, event_id)


def page(events, limit, after=None):
    _validate_limit(limit)
    cursor_key = _normalize_cursor(after)

    rows = []
    for row in events:
        key = (row['sequence'], row['event_id'])
        if cursor_key is not None and key <= cursor_key:
            continue
        rows.append((key, row))
    rows.sort(key=lambda pair: pair[0])

    selected = rows[:limit]
    items = [dict(row) for _, row in selected]
    if len(rows) > limit:
        last_key = selected[-1][0]
        next_cursor = [last_key[0], last_key[1]]
    else:
        next_cursor = None
    return {'items': items, 'next_cursor': next_cursor}
