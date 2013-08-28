from bottle import route, request

from ..models import package


@route('/submit', name='submit')
def submit_controller():
    old_version = request.query.old_version
    if old_version == '':
        old_version = None

    data = {
        'ip':                      request.remote_addr,
        'user_agent':              request.headers.get('User-Agent', ''),
        'package':                 request.query.package,
        'operation':               request.query.operation,
        'version':                 request.query.version,
        'old_version':             old_version,
        'package_control_version': request.query.package_control_version,
        'platform':                request.query.sublime_platform,
        'sublime_version':         request.query.sublime_version
    }

    package.usage.record(data)

    return {'result': 'success'}
