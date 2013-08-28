def filesize_abbr(this, num):
    """
    Pybars helper for generating the abbreviation of a filesize
    """
    break_points = [
        [1099511627776.0, 1,       'TB'],
        [1073741824.0,    1,       'GB'],
        [1048576.0,       1,       'MB'],
        [1024.0,          0,       'KB'],
        [1.0,             0,       'B']
    ]

    output = str(num)
    for (divisor, scale, suffix) in break_points:
        if num < divisor:
            continue
        output = ('{0:.' + str(scale) + 'f}').format(float(num) / divisor) + suffix
        break

    return output
