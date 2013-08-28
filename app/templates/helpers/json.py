import json as json_

import pybars


def json(this, data):
    """
    Pybars helper for generating raw JSON
    """

    return pybars.strlist( json_.dumps(data) )
