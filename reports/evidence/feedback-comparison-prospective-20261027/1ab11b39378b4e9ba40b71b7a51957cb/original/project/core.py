def apply_batch(stock, versions, changes):
    for change in changes:
        sku = change['sku']
        stock[sku] += change['delta']
        if versions[sku] != change['expected_version'] or stock[sku] < 0:
            raise ValueError('conflict')
        versions[sku] += 1
    return stock, versions
