def rolling_average(values, window):
    """Return the averages of all complete windows of length ``window``.

    ``window`` must be a positive integer (``bool`` is rejected).  When the
    window is larger than the input, or the input is empty, an empty list is
    returned.  The input sequence is never modified.
    """
    if isinstance(window, bool) or not isinstance(window, int):
        raise ValueError("window must be a positive integer")
    if window <= 0:
        raise ValueError("window must be a positive integer")

    items = list(values)
    if not items or window > len(items):
        return []

    result = []
    current = sum(items[:window])
    result.append(current / window)
    for index in range(window, len(items)):
        current += items[index] - items[index - window]
        result.append(current / window)
    return result
