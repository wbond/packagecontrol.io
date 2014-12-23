from bottle import route

from ..render import render_static


@route('/docs/events', name='events')
def events_controller():
    return render_static('docs/events')
