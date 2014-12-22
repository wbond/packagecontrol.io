from bottle import route

from ..render import render_static


@route('/docs/dependencies', name='dependencies')
def dependencies_controller():
    return render_static('docs/dependencies')
