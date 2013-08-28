from bottle import route

from ..render import render_static


@route('/docs/issues', name='issues')
def issues_controller():
    return render_static('docs/issues')
