from bottle import request, redirect, hook


@hook('before_request')
def remove_trailing_slash():
    # We don't ever redirect JSON requests since the trailing slash handling
    # is just for the purpose of making URLs human-friendly
    if request.environ.get('JSON'):
        return
    path = request.environ['PATH_INFO']
    if len(path) > 1 and path[-1] == '/':
        redirect(path.rstrip('/'), 301)

