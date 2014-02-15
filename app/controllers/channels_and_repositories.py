from bottle import route

from ..render import render_static


@route('/docs/channels_and_repositories', name='channels_and_repositories')
def channels_and_repositories_controller():
    return render_static('docs/channels_and_repositories')
