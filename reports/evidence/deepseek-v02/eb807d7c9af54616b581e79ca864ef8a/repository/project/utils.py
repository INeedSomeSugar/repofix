def overlaps(left, right):
    """Return True if closed intervals ``left`` and ``right`` overlap or touch.

    Both arguments are ``[start, end]`` pairs with ``start <= end``.
    """
    return right[0] <= left[1]
