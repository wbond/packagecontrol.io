from ...lib.homogenize_to_date import homogenize_to_date


def lt(this, options, val1, val2):
    """
    Pybars helper for seeing if a value is less than the other
    """

    is_none = val1 is None or val2 is None
    val2 = homogenize_to_date(val1, val2)
    if not is_none and val1 < val2:
        return options['fn'](this)
    else:
        return options['inverse'](this)
