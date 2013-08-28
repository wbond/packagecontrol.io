from bottle import route

from ..models import package
from ..render import render
from ..lib.paginating_controller import get_page, build_data


@route('/browse/updated', name='updated')
def updated_controller():
    page = get_page()
    per_page = 25

    results = package.find.updated(True, page, per_page)
    data = build_data(results, page, per_page)

    return render('updated', data)
