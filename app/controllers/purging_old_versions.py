from bottle import route

from ..render import render_static


@route('/docs/purging_old_versions', name='purging_old_versions')
def purging_old_versions_controller():
    return render_static('docs/purging_old_versions')
