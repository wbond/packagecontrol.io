from bottle import route

from ..render import render_static


@route('/docs/usage', name='usage')
def usage_controller():
    return render_static('docs/usage')
