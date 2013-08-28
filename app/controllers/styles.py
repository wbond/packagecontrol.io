from bottle import route

from ..render import render_static


@route('/docs/styles', name='styles')
def styles_controller():
    return render_static('docs/styles')
