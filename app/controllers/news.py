from bottle import route

from ..render import render_static


@route('/news', name='news')
def news_controller():
    return render_static('news')
