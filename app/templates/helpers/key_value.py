def key_value(this, options, obj):
    """
    Pybars helper for looping over an object
    """

    output = []
    for key, value in obj.items():
        output.extend(options['fn']({'key': key, 'value': value}))
    return output
