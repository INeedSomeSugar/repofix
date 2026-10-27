from .utils import overlaps


def merge_intervals(intervals):
    """Merge overlapping or touching closed intervals.

    The input sequence and its sub-lists are never mutated or reused; a new
    list of new two-element lists is returned, sorted by start point.
    """
    ordered = sorted((item[0], item[1]) for item in intervals)
    result = []
    for start, end in ordered:
        if result and overlaps(result[-1], (start, end)):
            if end > result[-1][1]:
                result[-1][1] = end
        else:
            result.append([start, end])
    return result
