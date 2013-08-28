import math


def split(this, options, values, groups):
    """
    Pybars helper for splitting an array of values
    """

    groups = int(groups)
    per_group = math.ceil(len(values) / groups)

    output = []
    for group in range(0, groups):
        start = group * per_group
        end = (group + 1) * per_group
        split_values = values[start:end]
        result = options['fn'](split_values)
        output.append(result)
    return output
