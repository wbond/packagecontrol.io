from bottle import route, request

import json

from ..lib.fetch_package_metadata import fetch_package_metadata
from ..render import render_error


@route('/fetch', name='fetch', method=['POST'])
def fetch_controller():
    if not request.environ.get('JSON'):
        return render_error('four_oh_four', __status_code__=404)

    try:
        data = request.body.read().decode('utf-8')
        result = fetch_package_metadata(json.loads(data))
    except UnicodeDecodeError as e:
        result = {'result': 'error', 'message': 'Error decoding JSON'}
    except ValueError as e:
        result = {'result': 'error', 'message': 'Error parsing JSON'}

    return result
