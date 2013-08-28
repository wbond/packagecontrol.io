from bottle import app


def export_routes():
    """
    Finds all of the named routes in the default bottle app and creates
    a data structure that can be serialized to JSON for usage in JS

    :return:
        A dict in the format:
        {
            route name: [
                {
                    'type': 'literal',
                    'value': string
                },
                {
                    'type': 'variable',
                    'name': name of variable,
                    'varType': data type of variable, 'str' or 'int'
                },
                ...
            ],
            ...
        }
    """

    _builder = app().router.builder

    routes = {}
    for key in _builder:
        if key.find('/') == -1:
            route = []
            pattern = _builder[key]
            for element in pattern:
                name, value = element

                if not name:
                    piece = {
                        'type': 'literal',
                        'value': value
                    }
                else:
                    piece = {
                        'type': 'variable',
                        'name': name,
                        'varType': value.__name__
                    }

                route.append(piece)
            routes[key] = route
    return routes
