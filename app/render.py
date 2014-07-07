import json

from bottle import request

from . import env
from . import config
from .template import template, static
from .lib.export_routes import export_routes


def render(name, data=None, **kwargs):
    """
    Renders data either to a template or JSON depending if JSON
    was specified as the file extension in the URL.

    :param name:
        The name of the template in the templates/ folder.

    :param data:
        A dict of the data to pass to the template. Alternatively,
        any number of keyword args can be passed.

    :return:
        An HTML string
    """

    if data == None:
        data = kwargs

    if request.environ.get('JSON'):
        return data

    data['exportedRoutes'] = export_routes()
    data['__template__'] = name
    data['__env__'] = env.name
    data['__version__'] = env.version
    if env.name == 'prod':
        data['__rollbar_client_key__'] = config.read_secret('rollbar_client_key')
    if '__status_code__' not in data:
        data['__status_code__'] = 200
    return template(name, data)


def render_error(name, data=None, **kwargs):
    """
    Renders an error - mostly just handles JSON for errors since
    bottle does not do that automatically.

    :param name:
        The name of the template in the templates/ folder.

    :param data:
        A dict of the data to pass to the template. Alternatively,
        any number of keyword args can be passed.

    :return:
        An HTML string
    """

    if data == None:
        data = kwargs

    if request.environ.get('JSON'):
        return json.dumps(data)

    return render(name, data)


def render_static(name):
    """
    Renders a static HTML page

    :param name:
        The name of the HTML file in the templates/ folder

    :return:
        An HTML string
    """

    data = {
        'html': static(name),
        'exportedRoutes': export_routes(),
        '__template__': name,
        '__status_code__': 200,
        '__env__': env.name,
        '__version__': env.version
    }
    if env.name == 'prod':
        data['__rollbar_client_key__'] = config.read_secret('rollbar_client_key')

    return template('static', data)
