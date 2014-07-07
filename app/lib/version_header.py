from bottle import response, hook

from .. import env


@hook('after_request')
def add_version(actual_response=None):
    if not actual_response:
        actual_response = response
    actual_response.headers['X-App-Version'] = env.version
    return actual_response
