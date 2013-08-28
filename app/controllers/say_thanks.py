from bottle import route

from ..render import render_static


@route('/say_thanks', name='say_thanks')
def say_thanks_controller():
    return render_static('say_thanks')
