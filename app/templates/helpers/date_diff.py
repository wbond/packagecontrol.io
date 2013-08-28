import calendar
import time
from datetime import datetime

from dateutil import parser


def date_diff(this, date, upper):
    """
    Pybars helper for generating a date diff
    """

    if not isinstance(date, datetime):
        date = parser.parse(date)

    first = int(calendar.timegm(date.timetuple()))
    second = int(time.time())

    diff = first - second

    if abs(diff) < 60:
        if upper:
            return 'Just now'
        return 'just now'

    break_points = [
        [3600,       60,       'minute', 'minutes'],
        [86400,      3600,     'hour',   'hours'],
        [604800,     86400,    'day',    'days'],
        [2592000,    604800,   'week',   'weeks'],
        [31536000,   2592000,  'month',  'months'],
        [2147483647, 31536000, 'year',   'years']
    ]

    for unit_info in break_points:
        if abs(diff) >= unit_info[0]:
            continue

        unit_diff = round(float(abs(diff)) / float(unit_info[1]))
        units = unit_info[2] if unit_diff == 1 else unit_info[3]
        break

    suffix = ' from now' if first > second else ' ago'
    diff_string = str(int(unit_diff)) + ' ' + units + suffix

    return diff_string
