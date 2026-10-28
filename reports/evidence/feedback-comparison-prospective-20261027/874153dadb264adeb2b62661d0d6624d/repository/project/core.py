def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def allocate_cents(total, weights):
    """Split ``total`` cents across ``weights`` using the largest remainder method.

    The magnitude ``abs(total)`` is distributed proportionally with exact integer
    arithmetic (floor shares plus one cent for the largest remainders, ties broken
    by ascending original index), then the sign of ``total`` is restored.
    """
    if not _is_int(total):
        raise ValueError("total must be an integer number of cents")

    if isinstance(weights, (str, bytes, bytearray)):
        raise ValueError("weights must be an iterable of integers")

    try:
        items = list(weights)
    except TypeError:
        raise ValueError("weights must be an iterable of integers")

    for weight in items:
        if not _is_int(weight):
            raise ValueError("weights must be integers")
        if weight < 0:
            raise ValueError("weights must be non-negative")

    if not items:
        if total == 0:
            return []
        raise ValueError("cannot allocate a non-zero total across no weights")

    denominator = sum(items)
    if denominator <= 0:
        raise ValueError("sum of weights must be positive")

    magnitude = abs(total)
    shares = []
    remainders = []
    for index, weight in enumerate(items):
        product = magnitude * weight
        shares.append(product // denominator)
        remainders.append((product % denominator, index))

    leftover = magnitude - sum(shares)
    if leftover:
        order = sorted(remainders, key=lambda pair: (-pair[0], pair[1]))
        for _, index in order[:leftover]:
            shares[index] += 1

    if total < 0:
        return [-share for share in shares]
    return shares
