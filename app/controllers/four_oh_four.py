from bottle import route, error

from ..render import render_error


@error(404)
def four_oh_four_controller(error):
    return render_error('four_oh_four', __status_code__=404)
