def num_abbr(this, num):
    """
    Pybars helper for generating the abbreviation of a number
    """
    break_points = [
        [1000000000000.0, 2,       'T'],
        [1000000000.0,    2,       'B'],
        [1000000.0,       2,       'M'],
        [1000.0,          0,       'K'],
        [1.0,             0,       '']
    ]

    if num is None:
        num = 0

    output = str(num)
    for (divisor, scale, suffix) in break_points:
        if num < divisor:
            continue
        output = ('{0:.' + str(scale) + 'f}').format(float(num) / divisor) + suffix
        break

    return output
