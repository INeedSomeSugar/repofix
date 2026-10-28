def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def apply_batch(stock, versions, changes):
    new_stock = dict(stock)
    new_versions = dict(versions)
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError('invalid change')
        try:
            sku = change['sku']
            delta = change['delta']
            expected_version = change['expected_version']
        except KeyError:
            raise ValueError('invalid change')
        if not _is_int(delta):
            raise ValueError('invalid delta')
        if not _is_int(expected_version) or expected_version < 0:
            raise ValueError('invalid expected_version')
        if sku not in new_stock or sku not in new_versions:
            raise KeyError(sku)
        if new_versions[sku] != expected_version:
            raise ValueError('version conflict')
        updated = new_stock[sku] + delta
        if updated < 0:
            raise ValueError('negative stock')
        new_stock[sku] = updated
        new_versions[sku] = new_versions[sku] + 1
    return new_stock, new_versions
