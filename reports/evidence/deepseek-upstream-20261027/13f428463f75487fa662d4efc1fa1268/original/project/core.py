# Excerpt from more-itertools 9ed3dbb0ae527230cd156d91d0af305478558fba; MIT License.
def one(iterable, too_short=None, too_long=None):
    """Return the first item from *iterable*, which is expected to contain only
    that item. Raise an exception if *iterable* is empty or has more than one
    item.

    :func:`one` is useful for ensuring that an iterable contains only one item.
    For example, it can be used to retrieve the result of a database query
    that is expected to return a single row.

    If *iterable* is empty, ``ValueError`` will be raised. You may specify a
    different exception with the *too_short* keyword:

        >>> it = []
        >>> one(it)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: too few items in iterable (expected 1)'
        >>> too_short = IndexError('too few items')
        >>> one(it, too_short=too_short)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        IndexError: too few items

    Similarly, if *iterable* contains more than one item, ``ValueError`` will
    be raised. You may specify a different exception with the *too_long*
    keyword:

        >>> it = ['too', 'many']
        >>> one(it)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: Expected exactly one item in iterable, but got 'too',
        'many', and perhaps more.
        >>> too_long = RuntimeError
        >>> one(it, too_long=too_long)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        RuntimeError

    Note that :func:`one` attempts to advance *iterable* twice to ensure there
    is only one item. See :func:`spy` or :func:`peekable` to check iterable
    contents less destructively.

    """
    iterator = iter(iterable)
    for first in iterator:
        for second in iterator:
            msg = (
                f'Expected exactly one item in iterable, but got {first!r}, '
                f'{second!r}, and perhaps more.'
            )
            raise too_long or ValueError(msg)
        return first
    raise too_short or ValueError('too few items in iterable (expected 1)')


def only(iterable, default=None, too_long=None):
    """If *iterable* has only one item, return it.
    If it has zero items, return *default*.
    If it has more than one item, raise the exception given by *too_long*,
    which is ``ValueError`` by default.

    >>> only([], default='missing')
    'missing'
    >>> only([1])
    1
    >>> only([1, 2])  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: Expected exactly one item in iterable, but got 1, 2,
     and perhaps more.'
    >>> only([1, 2], too_long=TypeError)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    TypeError

    Note that :func:`only` attempts to advance *iterable* twice to ensure there
    is only one item.  See :func:`spy` or :func:`peekable` to check
    iterable contents less destructively.

    """
    iterator = iter(iterable)
    for first in iterator:
        for second in iterator:
            msg = (
                f'Expected exactly one item in iterable, but got {first!r}, '
                f'{second!r}, and perhaps more.'
            )
            raise too_long or ValueError(msg)
        return first
    return default
