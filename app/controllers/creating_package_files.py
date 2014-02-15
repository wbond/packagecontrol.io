from bottle import route

from ..render import render_static


@route('/docs/creating_package_files', name='creating_package_files')
def creating_package_files_controller():
    return render_static('docs/creating_package_files')
