from bottle import route

from ..models import package
from ..render import render
from ..lib.paginating_controller import get_page, build_data


@route('/browse/popular', name='popular')
def popular_controller():
    page = get_page()
    per_page = 25

    results = package.find.top(True, page, per_page)
    data = build_data(results, page, per_page)

    return render('popular', data)
