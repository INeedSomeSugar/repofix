def overlaps(left, right):
    """Return True when closed intervals ``left`` and ``right`` overlap or touch.

    Both arguments are ``[start, end]`` pairs with ``start <= end``.  Closed
    intervals that merely share an endpoint (e.g. ``[1, 2]`` and ``[2, 3]``)
    are considered overlapping.
    """
    return right[0] <= left[1]
