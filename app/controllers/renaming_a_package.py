from bottle import route

from ..render import render_static


@route('/docs/renaming_a_package', name='renaming_a_package')
def renaming_a_package_controller():
    return render_static('docs/renaming_a_package')
