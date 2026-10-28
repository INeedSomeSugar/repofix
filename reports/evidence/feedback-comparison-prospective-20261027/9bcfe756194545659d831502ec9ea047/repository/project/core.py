def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def allocate_cents(total, weights):
    """Split ``total`` cents across ``weights`` using the largest remainder method.

    All arithmetic is exact integer arithmetic; no floating point is used.
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
        if not _is_int(weight) or weight < 0:
            raise ValueError("weights must be non-negative integers")

    if not items:
        if total == 0:
            return []
        raise ValueError("cannot allocate a non-zero total across no weights")

    denominator = sum(items)
    if denominator <= 0:
        raise ValueError("sum of weights must be positive")

    magnitude = abs(total)
    sign = -1 if total < 0 else 1

    shares = []
    remainders = []
    for index, weight in enumerate(items):
        product = magnitude * weight
        shares.append(product // denominator)
        remainders.append((product % denominator, index))

    leftover = magnitude - sum(shares)
    # Largest remainder first; ties broken by ascending original index.
    order = sorted(remainders, key=lambda pair: (-pair[0], pair[1]))
    for position in range(leftover):
        shares[order[position][1]] += 1

    return [sign * share for share in shares]
