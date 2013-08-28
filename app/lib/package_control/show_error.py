# Not shared with Package Control

from bottle import request
import rollbar

from ... import env


def show_error(string):
    """
    Sends an error message to

    :param string:
        The error to display
    """

    if env.is_prod():
        rollbar.report_message(string, 'error')
    else:
        print('ERROR: %s' % string)
