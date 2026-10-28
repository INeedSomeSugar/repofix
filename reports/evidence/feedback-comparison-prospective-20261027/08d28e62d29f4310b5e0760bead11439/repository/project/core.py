def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer between 1 and 100')
    if limit < 1 or limit > 100:
        raise ValueError('limit must be an integer between 1 and 100')
    return limit


def _normalize_cursor(after):
    if after is None:
        return None
    try:
        sequence, event_id = after
    except (TypeError, ValueError):
        raise ValueError('after must be a two-element sequence')
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise ValueError('after sequence must be an integer')
    if not isinstance(event_id, str):
        raise ValueError('after event_id must be a string')
    return (sequence, event_id)


def page(events, limit, after=None):
    limit = _validate_limit(limit)
    cursor_key = _normalize_cursor(after)

    rows = []
    for row in events:
        rows.append((row['sequence'], row['event_id'], row))
    rows.sort(key=lambda item: (item[0], item[1]))

    if cursor_key is not None:
        rows = [item for item in rows if (item[0], item[1]) > cursor_key]

    window = rows[:limit]
    items = [dict(item[2]) for item in window]

    next_cursor = None
    if len(rows) > len(window) and window:
        last = window[-1]
        next_cursor = [last[0], last[1]]

    return {'items': items, 'next_cursor': next_cursor}
