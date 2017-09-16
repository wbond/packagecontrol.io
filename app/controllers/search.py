import re
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
        terms = request.query.terms
        # Strip control chars and newlines
        terms = re.sub('[\x00-\x1f]', '', terms)
        # Encoding the terms as latin1 for the Location HTTP header
        terms = terms.encode('utf-8').decode('latin1')
        destination = url("search", terms=terms)
        return redirect(destination, 303)

    # URLs are always latin1 because of WSGI, but browsers tend to send UTF-8
    terms = bytes(terms, 'latin1').decode('utf-8', errors='ignore')

    # Remove zero-width punctuation
    terms = re.sub('[\u200b-\u200d]', '', terms)

    default_sort = 'relevance'
    sort = request.query.sort
    if not sort:
        sort = default_sort

    page = get_page()
    per_page = 25

    results = package.find.search(terms, sort, page, per_page)

    other_params = {}
    if sort != default_sort:
        other_params['sort'] = sort

    data = build_data(results, page, per_page, other_params=other_params)
    data['terms'] = terms
    data['sort'] = sort

    return render('search', data)
