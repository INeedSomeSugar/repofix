def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer between 1 and 100')
    if limit < 1 or limit > 100:
        raise ValueError('limit must be an integer between 1 and 100')
    return limit


def _cursor_key(after):
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
    cursor_key = _cursor_key(after)

    rows = sorted(
        (dict(row) for row in events),
        key=lambda row: (row['sequence'], row['event_id']),
    )
    if cursor_key is not None:
        rows = [row for row in rows if (row['sequence'], row['event_id']) > cursor_key]

    selected = rows[:limit]
    if len(rows) > limit:
        last = selected[-1]
        next_cursor = [last['sequence'], last['event_id']]
    else:
        next_cursor = None
    return {'items': selected, 'next_cursor': next_cursor}
