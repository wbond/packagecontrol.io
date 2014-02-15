from bottle import route

from ..render import render_static


@route('/docs/submitting_a_package', name='submitting_a_package')
def submitting_a_package_controller():
    return render_static('docs/submitting_a_package')
