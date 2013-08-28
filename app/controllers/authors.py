from bottle import route

from ..models import author
from ..render import render
from ..lib.paginating_controller import get_page, build_data


@route('/browse/authors', name='authors')
def authors_controller():
    page = get_page()
    per_page = 45

    results = author.list(True, page, per_page)
    data = build_data(results, page, per_page, 'authors')

    return render('authors', data)
