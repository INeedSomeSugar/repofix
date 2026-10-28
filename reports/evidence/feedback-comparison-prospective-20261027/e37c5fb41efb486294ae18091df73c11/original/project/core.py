def page(events, limit, after=None):
    events.sort(key=lambda row: row['sequence'])
    selected = events[:limit]
    if after is not None:
        selected = [row for row in selected if row['sequence'] > after[0]]
    cursor = [selected[-1]['sequence'], selected[-1]['event_id']] if selected else None
    return {'items': selected, 'next_cursor': cursor}
