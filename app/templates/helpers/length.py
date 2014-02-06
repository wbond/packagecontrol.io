def length(this, options, array, comparator, value):
    """
    Pybars helper for checking the length of an array
    """

    if comparator is None:
        comparator = 'gt'

    if value is None:
        value = 0

    if not isinstance(value, int):
        value = int(value)

    match = False

    if comparator == 'gt':
        match = len(array) > value
    elif comparator == 'gte':
        match = len(array) >= value
    elif comparator == 'lt':
        match = len(array) < value
    elif comparator == 'lte':
        match = len(array) <= value
    elif comparator == 'eq':
        match = len(array) == value
    elif comparator == 'ne':
        match = len(array) != value

    if match:
        return options['fn'](this)
    else:
        return options['inverse'](this)
