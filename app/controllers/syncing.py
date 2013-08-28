from bottle import route

from ..render import render_static


@route('/docs/syncing', name='syncing')
def syncing_controller():
    return render_static('docs/syncing')
