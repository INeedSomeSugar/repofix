def overlaps(left, right):
    """Return True when closed intervals ``left`` and ``right`` overlap or touch.

    Both arguments are ``[start, end]`` pairs with ``start <= end``.  Intervals
    that merely share an endpoint (e.g. ``[1, 2]`` and ``[2, 3]``) count as
    overlapping because the intervals are closed.
    """
    return right[0] <= left[1]
