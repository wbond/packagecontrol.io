from bottle import route, abort, request

from ..models import package
from ..models.not_found_error import NotFoundError
from ..render import render


@route('/packages/<name:re:(.*)>', name='package')
def package_controller(name):
    try:
        # URLs are always latin1 because of WSGI, but browsers tend to send UTF-8
        name = bytes(name, 'latin1').decode('utf-8')

        data = package.find.by_name(name)
        return render('package', data)

    except (NotFoundError) as e:
        abort(404, str(e))
