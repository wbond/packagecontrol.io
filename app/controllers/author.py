from bottle import route

from ..models import author
from ..render import render


@route('/browse/authors/<name:re:(.*)>', name='author')
def author_controller(name):
    # URLs are always latin1 because of WSGI, but browsers tend to send UTF-8
    name = bytes(name, 'latin1').decode('utf-8', errors='ignore')

    data = author.load(name)

    return render('author', data)
