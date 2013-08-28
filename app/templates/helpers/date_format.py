from datetime import datetime

from dateutil import parser


def date_format(this, date, format):
    """
    Pybars helper for formatting a date
    """

    if not isinstance(date, datetime):
        date = parser.parse(str(date))

    if format == 'ISO':
        format = '%FT%TZ'

    format = format.replace('%F', '%Y-%m-%d')
    format = format.replace('%T', '%H:%M:%S')
    output = date.strftime(format)
    return output
