from bottle import route

from ..render import render_static


@route('/docs/settings', name='settings')
def settings_controller():
    return render_static('docs/settings')
