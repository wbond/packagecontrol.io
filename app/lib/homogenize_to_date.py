import re
from datetime import datetime, timedelta


def homogenize_to_date(val1, val2):
    if isinstance(val1, datetime) and isinstance(val2, str):
        results = re.findall('(([+\-]?\d+)\s*(years?|months?|days?|hours?|minutes?|seconds?)|today|now|bod|eod)', val2, re.I)
        date = datetime.utcnow()

        if not results:
            raise Exception('Invalid adjustment, must be in the form: +1 year, -3 days, +30 seconds, +2 days eod')

        for result in results:
            lower_result = result[0].lower()

            if lower_result in ['today', 'now']:
                date = datetime.utcnow()

            # Explicit Beginning Of Day and End Of Day values use UTC,
            # everything else is relative
            elif lower_result == 'bod':
                date.setUTCHours(0)
                date.setUTCMinutes(0)
                date.setUTCSeconds(0)

            elif lower_result == 'eod':
                date.setUTCHours(23)
                date.setUTCMinutes(59)
                date.setUTCSeconds(59)

            else:
                amount = int(result[1])
                unit = re.sub('s$', '', result[2].lower())

                if unit == 'year':
                    interval = timedelta(years=amount)
                elif unit == 'month':
                    interval = timedelta(months=amount)
                elif unit == 'day':
                    interval = timedelta(days=amount)
                elif unit == 'hour':
                    interval = timedelta(hours=amount)
                elif unit == 'minute':
                    interval = timedelta(minutes=amount)
                elif unit == 'second':
                    interval = timedelta(seconds=amount)
                date += interval

        val2 = date

    return val2
