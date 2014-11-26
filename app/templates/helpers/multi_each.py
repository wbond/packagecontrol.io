def multi_each(this, options, list_1, list_2):
    """
    Pybars helper for looping over two lists at the same time
    """

    output = []
    i = 0
    while i < max(len(list_1), len(list_2)):
        try:
            value_1 = list_1[i]
        except (IndexError):
            value_1 = None
        try:
            value_2 = list_2[i]
        except (IndexError):
            value_2 = None
        output.extend(options['fn']({'value_1': value_1, 'value_2': value_2, '@index': i}))
        i += 1
    return output
