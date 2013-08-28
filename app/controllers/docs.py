from bottle import route

from ..render import render_static


@route('/docs', name='docs')
def docs_controller():
    return render_static('docs')
