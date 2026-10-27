def overlaps(left, right):
    """Return True when closed intervals left and right share at least one point.

    Endpoints that merely touch (right start == left end) count as overlapping.
    """
    return right[0] <= left[1]
