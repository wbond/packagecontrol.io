from bottle import route, request, abort, response

import json

from ..lib.run_repo_tests import test_pull_request
from ..render import render_error


@route('/test_pr/<pr:re:(\d+)>', name='test_pr', method=['POST'])
def test_pr_controller(pr):
    if not request.environ.get('JSON'):
        abort(404)

    result = test_pull_request(pr)
    if result['result'] == 'error':
        response.status = 500
        return result
    return result
