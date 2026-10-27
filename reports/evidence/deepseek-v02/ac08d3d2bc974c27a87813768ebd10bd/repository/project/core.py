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

    data = list(values)
    if not data or window > len(data):
        return []

    total = sum(data[:window])
    result = [total / window]
    for index in range(window, len(data)):
        total += data[index] - data[index - window]
        result.append(total / window)
    return result
