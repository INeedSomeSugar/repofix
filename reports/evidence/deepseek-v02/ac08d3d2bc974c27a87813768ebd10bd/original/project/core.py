def rolling_average(values, window):
    return [sum(values[max(0, i - window):i + 1]) / window
            for i in range(len(values))]
