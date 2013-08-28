Snakeskin.Dates.adjust = (date, adjustment) ->
  if _.isString(date) and _.isUndefined(adjustment)
    adjustment = date
    date = new Date()

  regex = /([+\-]?\d+)\s*(years?|months?|days?|hours?|minutes?|seconds?)|today|now|bod|eod/gi

  result = regex.exec(adjustment)
  if not result
    throw new Error('Invalid adjustment, must be in the form: +1 year, -3 days, +30 seconds, +2 days eod')

  while result
    lowerResult = result[0].toLowerCase()

    if lowerResult in ['today', 'now']
      date = new Date()

    # Explicit Beginning Of Day and End Of Day values use UTC,
    # everything else is relative
    else if lowerResult == 'bod'
      date.setUTCHours(0)
      date.setUTCMinutes(0)
      date.setUTCSeconds(0)

    else if lowerResult == 'eod'
      date.setUTCHours(23)
      date.setUTCMinutes(59)
      date.setUTCSeconds(59)

    else
      amount = parseInt(result[1])
      unit = result[2].toLowerCase().replace(/s$/, '')

      if unit == 'year'
        date.setFullYear(date.getFullYear() + amount)
      else if unit == 'month'
        date.setMonth(date.getMonth() + amount)
      else if unit == 'day'
        date.setDate(date.getDate() + amount)
      else if unit == 'hour'
        date.setHours(date.getHours() + amount)
      else if unit == 'minute'
        date.setMinutes(date.getMinutes() + amount)
      else if unit == 'second'
        date.setSeconds(date.getSeconds() + amount)

    result = regex.exec(adjustment)

  return date


Snakeskin.Dates.parseISO8601 = (string) ->
  regex = ///
    ^\s*
    (\d{4})        # Year
    -(\d{2})       # Month
    -(\d{2})       # Day
    (?:
      [\sT]          # Date/time separator
      (\d{2})        # Hour (24)
      (?::(\d{2}))?  # Minutes
      (?::(\d{2}))?  # Seconds
      (?:\.(\d+))?   # Seconds fraction
      (Z)?           # UTC indicator
    )?
    \s*$
  ///

  match = string.match(regex)
  if not match
    return null

  for index in [4, 5, 6]
    if not match[index]
      match[index] = 0

  if match[7]
    if match[7].length > 3
      match[7] = match[7].substring(0, 3)
    while match[7].length < 3
      match[7] += '0'
    match[7] = parseInt(match[7])
  else
    match[7] = 0

  if match[8]
    date = new Date(Date.UTC(
      match[1],
      parseInt(match[2]) - 1,
      match[3],
      match[4],
      match[5],
      match[6],
      match[7]
    ))
  else
    date =  new Date(
      match[1],
      parseInt(match[2]) - 1,
      match[3],
      match[4],
      match[5],
      match[6],
      match[7]
    )
  return date


# Methods used by format()
pad = (value) ->
  value = String(value)
  if value.length == 1
    return '0' + value
  return value

call = (date, utc, method) ->
  if utc
    return date['getUTC' + method]()
  return date['get' + method]()

getYear = (date, utc) ->
  call(date, utc, 'FullYear')

getMonth = (date, utc) ->
  call(date, utc, 'Month')

getDate = (date, utc) ->
  call(date, utc, 'Date')

getDay = (date, utc) ->
  call(date, utc, 'Day')

getHours = (date, utc) ->
  call(date, utc, 'Hours')

getMinutes = (date, utc) ->
  call(date, utc, 'Minutes')

getSeconds = (date, utc) ->
  call(date, utc, 'Seconds')

get12Hours = (date, utc) ->
  hours = call(date, utc, 'Hours')
  if hours == 0
    return 12
  if hours > 12
    return hours - 12
  return hours

getAmPm = (date, utc) ->
  if call(date, utc, 'Hours') >= 12
    return 'PM'
  return 'AM'

formattingMethods = {
  '%a': (date, utc) ->
    {
      0: 'Sun',       1: 'Mon',       2: 'Tue',
      3: 'Wed',       4: 'Thu',       5: 'Fri',
      6: 'Sat'
    }[getDay(date, utc)]

  '%A': (date, utc) ->
    {
      0: 'Sunday',    1: 'Monday',    2: 'Tuesday',
      3: 'Wednesday', 4: 'Thursday',  5: 'Friday',
      6: 'Saturday'
    }[getDay(date, utc)]

  '%b': (date, utc) ->
    {
      0: 'Jan',       1: 'Feb',       2: 'Mar',
      3: 'Apr',       4: 'May',       5: 'Jun',
      6: 'Jul',       7: 'Aug',       8: 'Sep',
      9: 'Oct',      10: 'Nov',      11: 'Dec'
    }[getMonth(date, utc)]

  '%B': (date, utc) ->
    {
      0: 'January',   1: 'February',  2: 'March',
      3: 'April',     4: 'May',       5: 'June',
      6: 'July',      7: 'August',    8: 'September',
      9: 'October',  10: 'November', 11: 'December'
    }[getMonth(date, utc)]

  '%d': (date, utc) ->
    pad(getDate(date, utc))

  '%-d': getDate

  '%F': (date, utc) ->
    out = getYear(date, true)
    out += '-' + pad(getMonth(date, true) + 1)
    out += '-' + pad(getDate(date, true))
    out

  '%H': (date, utc) ->
    pad(getHours(date, utc))

  '%-H': getHours

  '%I': (date, utc) ->
    pad(get12Hours(date, utc))

  '%-I': get12Hours

  '%m': (date, utc) ->
    pad(getMonth(date, utc) + 1)

  '%-m': (date, utc) ->
    getMonth(date, utc) + 1

  '%M': (date, utc) ->
    pad(getMinutes(date, utc))

  '%-M': getMinutes

  '%p': getAmPm

  '%s': (date, utc) ->
    date.getTime() / 1000

  '%S': (date, utc) ->
    pad(getSeconds(date, utc))

  '%-S': getSeconds

  '%t': (date, utc) ->
    year           = getHour(date, utc)
    divFour        = year % 4 == 0
    divHundred     = year % 100 == 0
    divFourHundred = year % 400 == 0

    leapYear = divFour and (not divHundred or divFourHundred)
    febDays  = if leapYear then 29 else 28

    {
      0: 31,  1: febDays,  2: 31
      3: 30,  4: 31,       5: 30
      6: 31,  7: 31,       8: 30
      9: 31, 10: 30,      11: 31
    }[getMonth(date, utc)]

  '%T': (date, utc) ->
    out = pad(getHours(date, true))
    out += ':' + pad(getMinutes(date, true))
    out += ':' + pad(getSeconds(date, true))
    out

  '%y': (date, utc) ->
    String(dateYear(date, utc)).substr(2, 2)

  '%Y': getYear

  '%%': (date, utc) ->
    '%'
}


Snakeskin.Dates.format = (date, format, utc) ->
  if _.isString(date)
    date = Snakeskin.Dates.parseISO8601(date)

  output = format
  matches = format.match(/(%-[dHImMS]|%[%aAbBdFHImMpsStTyY])/g)

  if not matches
    return format

  for match in matches
    replacement = formattingMethods[match](date, utc)
    output = output.replace(match, replacement)

  output


Snakeskin.Dates.diff = (date, upper) ->
  if _.isString(date)
    date = Snakeskin.Dates.parseISO8601(date)

  start = date.getTime() / 1000
  end = new Date().getTime() / 1000

  diff = start - end

  if Math.abs(start - end) < 60
    if upper
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

  for unit_info in break_points
    if Math.abs(diff) >= unit_info[0]
      continue

    unit_diff = Math.round(parseFloat(Math.abs(diff)) / parseFloat(unit_info[1]))
    units = if unit_diff == 1 then unit_info[2] else unit_info[3]
    break

  suffix = if start > end then ' from now' else ' ago'
  return parseInt(unit_diff) + ' ' + units + suffix


Snakeskin.Dates.homogenizeTo = (val1, val2) ->
  if _.isDate(val1) and _.isString(val2)
    try
      val2 = Snakeskin.Dates.adjust(val2)
    catch e
  return val2
