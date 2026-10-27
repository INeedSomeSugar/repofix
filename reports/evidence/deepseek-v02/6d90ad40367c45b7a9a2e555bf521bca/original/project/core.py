from .utils import overlaps


def merge_intervals(intervals):
    intervals.sort()
    result = []
    for item in intervals:
        if result and overlaps(result[-1], item):
            result[-1][1] = max(result[-1][1], item[1])
        else:
            result.append(item)
    return result
