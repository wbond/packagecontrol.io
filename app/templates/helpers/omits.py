def omits(this, options, array, *values):
    """
    Pybars helper for seeing if an array omits one or more values
    """

    is_none = array is None

    omits = False
    if not is_none:
        omits = True
        for value in values:
            if value in array:
                omits = False
                break

    if not is_none and omits:
        return options['fn'](this)
    else:
        return options['inverse'](this)
