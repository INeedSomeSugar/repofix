def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError('limit must be an integer between 1 and 100')
    if limit < 1 or limit > 100:
        raise ValueError('limit must be an integer between 1 and 100')


def _parse_cursor(after):
    if after is None:
        return None
    try:
        sequence, event_id = after
    except (TypeError, ValueError):
        raise ValueError('after must be a two-element sequence')
    return (sequence, event_id)


def page(events, limit, after=None):
    _validate_limit(limit)
    cursor_key = _parse_cursor(after)

    ordered = sorted(
        events,
        key=lambda row: (row['sequence'], row['event_id']),
    )
    if cursor_key is not None:
        ordered = [
            row for row in ordered
            if (row['sequence'], row['event_id']) > cursor_key
        ]

    selected = ordered[:limit]
    items = [dict(row) for row in selected]
    if len(ordered) > limit:
        last = selected[-1]
        next_cursor = [last['sequence'], last['event_id']]
    else:
        next_cursor = None
    return {'items': items, 'next_cursor': next_cursor}
