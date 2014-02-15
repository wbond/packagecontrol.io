from bottle import route

from ..render import render_static


@route('/docs/messaging', name='messaging')
def messaging_controller():
    return render_static('docs/messaging')
