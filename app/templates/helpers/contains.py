def contains(this, options, array, *values):
    """
    Pybars helper for seeing if an array contains one or more values
    """

    is_none = array is None

    contains = False
    if not is_none:
        contains = True
        for value in values:
            if value not in array:
                contains = False
                break

    if not is_none and contains:
        return options['fn'](this)
    else:
        return options['inverse'](this)
