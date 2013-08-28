from bottle import route

from ..render import render_static


@route('/docs/code', name='code')
def code_controller():
    return render_static('docs/code')
