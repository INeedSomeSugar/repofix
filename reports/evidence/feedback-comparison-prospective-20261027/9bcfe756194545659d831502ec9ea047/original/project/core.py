def allocate_cents(total, weights):
    denominator = sum(weights)
    return [int(total * weight / denominator) for weight in weights]
