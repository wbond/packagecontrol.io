from bottle import route

from ..render import render_static


@route('/docs/troubleshooting', name='troubleshooting')
def troubleshooting_controller():
    return render_static('docs/troubleshooting')
