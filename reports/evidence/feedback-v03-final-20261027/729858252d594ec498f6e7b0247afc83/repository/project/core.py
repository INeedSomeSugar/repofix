def rolling_average(values, window):
    if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
        raise ValueError("window must be a positive integer")
    return [sum(values[i:i + window]) / window
            for i in range(len(values) - window + 1)]
