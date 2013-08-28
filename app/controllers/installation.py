from bottle import route

from ..render import render_static


@route('/installation', name='installation')
def installation_controller():
    return render_static('installation')
