def num_format(this, num, scale=0):
    """
    Pybars helper for formatting a number
    """

    if num is None:
        num = 0
    output = ('{0:,.' + str(scale) + 'f}').format(float(num))
    # Strip trailing zeros
    return output.rstrip('0').rstrip('.') if '.' in output else output
