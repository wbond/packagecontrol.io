import math
import urllib.parse

from bottle import route, request, redirect, url

from ..models import package
from ..render import render
from ..lib.paginating_controller import get_page, build_data


@route('/search', name='search_blank')
@route('/search/<terms:re:(.*)>', name='search')
def search_controller(terms=''):
    # This allows users without JS to search
    if request.query.terms:
        # Encoding the terms as latin1 for the Location HTTP header
        terms = request.query.terms.encode('utf-8').decode('latin1')
        destination = url("search", terms=terms)
        return redirect(destination, 303)

    # URLs are always latin1 because of WSGI, but browsers tend to send UTF-8
    terms = bytes(terms, 'latin1').decode('utf-8', errors='ignore')

    page = get_page()
    per_page = 25

    results = package.find.search(terms, page, per_page)

    data = build_data(results, page, per_page)
    data['terms'] = terms

    return render('search', data)
