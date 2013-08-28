import html

import pybars


def highlight(this, string):
    """
    Pybars helper to convert highlighting characters (\x02 and \x03) into
    bold HTML tags
    """

    string = html.escape(string).replace("\x02", '<b>').replace("\x03", '</b>')
    return pybars.strlist(string)
