def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def allocate_cents(total, weights):
    """Split ``total`` cents across ``weights`` using the largest remainder method.

    The magnitude ``abs(total)`` is distributed proportionally (floor), then the
    remaining cents go to the largest exact remainders, ties broken by ascending
    original index.  The sign of ``total`` is restored afterwards.  All arithmetic
    is exact integer arithmetic (no floating point).
    """
    if not _is_int(total):
        raise ValueError("total must be an integer number of cents (not bool)")

    if isinstance(weights, (str, bytes, bytearray)):
        raise ValueError("weights must be an iterable of integers")

    try:
        items = list(weights)
    except TypeError:
        raise ValueError("weights must be an iterable of integers")

    for weight in items:
        if not _is_int(weight):
            raise ValueError("each weight must be an integer (not bool)")
        if weight < 0:
            raise ValueError("weights must be non-negative")

    if not items:
        if total == 0:
            return []
        raise ValueError("cannot allocate a non-zero total across no weights")

    denominator = sum(items)
    if denominator <= 0:
        raise ValueError("sum of weights must be greater than zero")

    magnitude = abs(total)
    shares = []
    remainders = []
    for index, weight in enumerate(items):
        product = magnitude * weight
        shares.append(product // denominator)
        remainders.append((product % denominator, index))

    leftover = magnitude - sum(shares)
    if leftover:
        # Largest remainder first, ties by ascending original index.
        order = sorted(remainders, key=lambda pair: (-pair[0], pair[1]))
        for _, index in order[:leftover]:
            shares[index] += 1

    if total < 0:
        shares = [-share for share in shares]

    return shares
