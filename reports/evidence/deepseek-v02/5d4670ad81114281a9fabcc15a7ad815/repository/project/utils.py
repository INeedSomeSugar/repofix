def overlaps(left, right):
    """Return True if closed intervals left and right overlap or touch.

    Both intervals are expected to be (start, end) pairs with start <= end.
    Touching endpoints (right start == left end) count as overlapping.
    """
    return right[0] <= left[1]
