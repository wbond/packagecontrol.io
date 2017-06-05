from bottle import route, request

import json

from ..lib.run_repo_tests import run_tests, build_result, format_report
from ..render import render


@route('/test_repo', name='test_repo', method=['POST', 'GET'])
def test_repo_controller():
    if not request.environ.get('JSON') or request.method == 'GET':
        return render('test_repo')

    try:
        data = request.body.read().decode('utf-8')
        data = json.loads(data)
    except UnicodeDecodeError as e:
        result = build_result([format_report('Error decoding JSON')], [])
    except ValueError as e:
        result = build_result([format_report('Error parsing JSON')], [])

    return run_tests(data)
