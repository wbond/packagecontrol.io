from bottle import request, redirect, hook


@hook('before_request')
def remove_trailing_slash():
    path = request.environ['PATH_INFO']
    if len(path) > 1 and path[-1] == '/':
        redirect(path.rstrip('/'), 301)

