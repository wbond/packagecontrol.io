from bottle import route

from ..models import label
from ..render import render
from ..lib.paginating_controller import get_page, build_data


@route('/browse/labels', name='labels')
def labels_controller():
    page = get_page()
    per_page = 200

    results = label.list(True, page, per_page)
    data = build_data(results, page, per_page, 'labels')

    return render('labels', data)
