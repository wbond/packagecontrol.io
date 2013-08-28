from bottle import route, error

from ..render import render_error


@error(500)
def five_hundred_controller(error):
    return render_error('five_hundred', __status_code__=500)
