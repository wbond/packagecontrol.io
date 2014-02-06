def eq(this, options, val1, val2, *values):
    """
    Pybars helper for seeing if a value is equal the other
    """

    # Allow comparing two lists
    if val2 and values:
        values = list(values)
        values.append(val2)
        val2 = sorted(values)
        if val1:
            val1 = sorted(val1)

    if isinstance(val1, list) and len(val1) == 1 and not isinstance(val2, list) and val1[0] == val2:
        val2 = [val2]

    is_none = val1 is None or val2 is None
    if not is_none and val1 == val2:
        return options['fn'](this)
    else:
        return options['inverse'](this)
