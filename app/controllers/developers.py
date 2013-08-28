from bottle import route

from ..render import render_static


@route('/docs/developers', name='developers')
def developers_controller():
    return render_static('docs/developers')
