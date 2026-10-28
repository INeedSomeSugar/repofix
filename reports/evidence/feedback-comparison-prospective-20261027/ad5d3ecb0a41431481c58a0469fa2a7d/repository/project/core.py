def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_stock(stock):
    if not isinstance(stock, dict):
        raise ValueError('stock must be a dict')
    for sku, qty in stock.items():
        if not _is_int(qty) or qty < 0:
            raise ValueError('invalid stock quantity for %r' % (sku,))
    return dict(stock)


def _validate_versions(versions):
    if not isinstance(versions, dict):
        raise ValueError('versions must be a dict')
    for sku, ver in versions.items():
        if not _is_int(ver) or ver < 0:
            raise ValueError('invalid version for %r' % (sku,))
    return dict(versions)


def apply_batch(stock, versions, changes):
    new_stock = _validate_stock(stock)
    new_versions = _validate_versions(versions)
    if changes is None:
        raise ValueError('changes must be iterable')
    try:
        iterator = iter(changes)
    except TypeError:
        raise ValueError('changes must be iterable')
    for change in iterator:
        if not isinstance(change, dict):
            raise ValueError('each change must be a dict')
        for key in ('sku', 'delta', 'expected_version'):
            if key not in change:
                raise ValueError('missing key %r in change' % (key,))
        sku = change['sku']
        delta = change['delta']
        expected_version = change['expected_version']
        if not _is_int(delta):
            raise ValueError('delta must be an int')
        if not _is_int(expected_version) or expected_version < 0:
            raise ValueError('expected_version must be a non-negative int')
        if sku not in new_stock or sku not in new_versions:
            raise KeyError(sku)
        if new_versions[sku] != expected_version:
            raise ValueError('version conflict for %r' % (sku,))
        updated = new_stock[sku] + delta
        if updated < 0:
            raise ValueError('negative stock for %r' % (sku,))
        new_stock[sku] = updated
        new_versions[sku] = new_versions[sku] + 1
    return new_stock, new_versions
