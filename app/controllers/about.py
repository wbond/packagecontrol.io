from bottle import route

from ..render import render_static


@route('/about', name='about')
def about_controller():
    return render_static('about')
