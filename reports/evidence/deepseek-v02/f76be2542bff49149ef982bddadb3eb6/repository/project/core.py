from .utils import overlaps


def merge_intervals(intervals):
    """Merge overlapping or endpoint-touching closed intervals.

    The input is never mutated and the returned list contains freshly created
    ``[start, end]`` lists sorted by start.
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
