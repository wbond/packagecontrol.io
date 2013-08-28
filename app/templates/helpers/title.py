import html

import pybars


def title(this, *values):
    """
    Pybars helper for setting the page title
    """

    values = [html.escape(value) for value in values if value not in ['', None]]
    return pybars.strlist("{{title}}" + " - ".join(values) + "{{/title}}")
