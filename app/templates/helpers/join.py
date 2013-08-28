import html

import pybars


def join(this, values, separator):
    """
    Pybars helper for joining an array of values
    """

    values = [html.escape(str(value)) for value in values]
    return pybars.strlist(separator.join(values))
