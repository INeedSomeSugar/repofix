from .utils import overlaps


def merge_intervals(intervals):
    """Merge overlapping or endpoint-touching closed intervals.

    ``intervals`` is a sequence of ``[start, end]`` pairs with
    ``start <= end``.  The input is never mutated and no input sub-list is
    reused in the result: every returned interval is a fresh list.  The result
    is sorted by start (then end) and contains only disjoint, non-touching
    intervals.  An empty input yields ``[]``.
    """
    ordered = sorted([item[0], item[1]] for item in intervals)
    result = []
    for item in ordered:
        if result and overlaps(result[-1], item):
            if item[1] > result[-1][1]:
                result[-1][1] = item[1]
        else:
            result.append([item[0], item[1]])
    return result
