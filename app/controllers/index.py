from bottle import route

from ..models import package, label, author
from ..render import render


@route('/', name='index')
def index_controller():
    data = {
        'labels': label.list(),
        'new': package.find.new(),
        'top': package.find.top_100_random(),
        'trending': package.find.trending()
    }

    return render('index', data)
