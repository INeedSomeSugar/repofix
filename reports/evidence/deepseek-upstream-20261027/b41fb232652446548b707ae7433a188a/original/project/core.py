# Excerpt from more-itertools bc8be1013ac90fe3c1df8aae646b02605d578818; MIT License.
def value_chain(*args):
    """Yield all arguments passed to the function in the same order in which
    they were passed. If an argument itself is iterable then iterate over its
    values.

        >>> list(value_chain(1, 2, 3, [4, 5, 6]))
        [1, 2, 3, 4, 5, 6]

    Binary and text strings are not considered iterable and are emitted
    as-is:

        >>> list(value_chain('12', '34', ['56', '78']))
        ['12', '34', '56', '78']

    Pre- or postpend a single element to an iterable:

        >>> list(value_chain(1, [2, 3, 4, 5, 6]))
        [1, 2, 3, 4, 5, 6]
        >>> list(value_chain([1, 2, 3, 4, 5], 6))
        [1, 2, 3, 4, 5, 6]

    Multiple levels of nesting are not flattened.

    """
    scalar_types = (str, bytes)
    for value in args:
        if isinstance(value, scalar_types):
            yield value
            continue
        try:
            yield from value
        except TypeError:
            yield value
