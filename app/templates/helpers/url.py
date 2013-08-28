import urllib.parse

import bottle


def url(this, route, **kwargs):
    """
    Pybars helper for generating a URL
    """

    new_args = {}
    for name, value in kwargs.items():
        new_args[name] = urllib.parse.quote(str(value), safe='', encoding='UTF-8', errors=None)

    return bottle.url(route, **new_args)
