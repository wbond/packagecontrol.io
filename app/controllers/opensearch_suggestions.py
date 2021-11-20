import json

from bottle import route, response

from ..models import package


@route('/opensearch_suggestions', name='opensearch_suggestions_blank')
@route('/opensearch_suggestions/<terms:re:(.*)>', name='opensearch_suggestions')
def opensearch_suggestions_controller(terms=''):
    # TODO: Optimize this call, since we're requesting a lot of stuff we don't need
    results = package.find.search(terms, 'relevance', 1, 10)

    # Convert data to match suggestion extension format
    # https://github.com/dewitt/opensearch/blob/master/mediawiki/Specifications/OpenSearch/Extensions/Suggestions/1.1/Draft%201.wiki
    data = [terms, [package['name'] for package in results['packages']]]

    # Manually convert to JSON, since the response is a list and not a dict
    response.content_type = 'application/x-suggestions+json'
    return json.dumps(data)
