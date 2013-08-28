import hashlib
from datetime import datetime

from bottle import route, response, url

from ..models import package
from ..render import render


@route('/browse/new/rss', name='rss')
def rss_controller():
    now = datetime.utcnow()
    today = now.date()

    result = package.find.new(True, 1, 25)
    for package_ in result['packages']:
        package_['md5'] = hashlib.md5(package_['name'].encode('utf-8')).hexdigest()

    data = {
        'packages': result['packages'],
        'year': today.strftime('%Y')
    }

    response.content_type = 'application/xml; charset=UTF-8'
    return render('rss', data)
