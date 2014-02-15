from bottle import route

from ..render import render_static


@route('/docs/customizing_packages', name='customizing_packages')
def customizing_packages_controller():
    return render_static('docs/customizing_packages')
