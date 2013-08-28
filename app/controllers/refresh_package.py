from bottle import route, request

from ..models import package
from ..lib.refresh_packages import refresh_packages


@route('/refresh_package', name='refresh_package')
def refresh_package_controller():
    valid_sources = package.sources.dependent_sources(request.query.source)

    refresh_packages(valid_sources)

    return None
