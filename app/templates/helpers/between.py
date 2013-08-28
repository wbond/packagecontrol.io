from ...lib.homogenize_to_date import homogenize_to_date


def between(this, options, val1, val2, val3):
    """
    Pybars helper for seeing if a value is between the other two
    """

    is_none = val1 is None or val2 is None or val3 is None
    val2 = homogenize_to_date(val1, val2)
    val3 = homogenize_to_date(val1, val3)
    if not is_none and val2 <= val1 <= val3:
        return options['fn'](this)
    else:
        return options['inverse'](this)
