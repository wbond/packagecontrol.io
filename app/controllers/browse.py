from bottle import route

from ..models import package, label, author
from ..render import render


@route('/browse', name='browse')
def browse_controller():
    data = {
        'labels': label.list(),
        'new': package.find.new(),
        'updated': package.find.updated(),
        'top': package.find.top(),
        'trending': package.find.trending(),
        'authors': author.list()
    }

    return render('browse', data)
