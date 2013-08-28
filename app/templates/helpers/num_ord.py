def num_ord(this, num):
    """
    Pybars helper for printing a number with its ordinal suffix
    """

    mod = num % 10
    if 10 < num < 14:
      suffix = 'th'
    elif mod == 1:
      suffix = 'st'
    elif mod == 2:
      suffix = 'nd'
    elif mod == 3:
      suffix = 'rd'
    else:
      suffix = 'th'
    return str(num) + suffix
