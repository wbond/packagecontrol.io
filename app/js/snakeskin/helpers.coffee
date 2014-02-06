class window.Snakeskin.Helpers

  @register: ->
    Handlebars.registerHelper('lt', @lt)
    Handlebars.registerHelper('lte', @lte)
    Handlebars.registerHelper('gt', @gt)
    Handlebars.registerHelper('gte', @gte)
    Handlebars.registerHelper('eq', @eq)
    Handlebars.registerHelper('ne', @ne)
    Handlebars.registerHelper('contains', @contains)
    Handlebars.registerHelper('omits', @omits)
    Handlebars.registerHelper('between', @between)
    Handlebars.registerHelper('length', @len)

    Handlebars.registerHelper('date_diff', @dateDiff)
    Handlebars.registerHelper('date_format', @dateFormat)

    Handlebars.registerHelper('split', @split)
    Handlebars.registerHelper('join', @join)
    Handlebars.registerHelper('highlight', @highlight)
    Handlebars.registerHelper('key_value', @keyValue)
    Handlebars.registerHelper('num_abbr', @numAbbr)
    Handlebars.registerHelper('num_format', @numFormat)
    Handlebars.registerHelper('num_ord', @numOrd)
    Handlebars.registerHelper('filesize_abbr', @filesizeAbbr)
    Handlebars.registerHelper('url_abbr', @urlAbbr)
    Handlebars.registerHelper('word_wrap', @wordWrap)
    Handlebars.registerHelper('title', @title)

  @lt: (val1, val2, options) ->
    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    val2 = Snakeskin.Dates.homogenizeTo(val1, val2)
    Handlebars.helpers['if'].call(this, not isNone and val1 < val2, options)

  @lte: (val1, val2, options) ->
    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    val2 = Snakeskin.Dates.homogenizeTo(val1, val2)
    Handlebars.helpers['if'].call(this, not isNone and val1 <= val2, options)

  @gt: (val1, val2, options) ->
    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    val2 = Snakeskin.Dates.homogenizeTo(val1, val2)
    Handlebars.helpers['if'].call(this, not isNone and val1 > val2, options)

  @gte: (val1, val2, options) ->
    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    val2 = Snakeskin.Dates.homogenizeTo(val1, val2)
    Handlebars.helpers['if'].call(this, not isNone and val1 >= val2, options)

  @eq: (val1, val2, values...) ->
    options = values.pop()

    if values
      values.push(val2)
      val2 = _.clone(values).sort()
      if _.isArray(val1)
        # We copy the value to prevent modifying the original
        val1 = _.clone(val1).sort()

    # Allow comparing an array with a scalar value if the array has a single value
    if _.isArray(val1) and val1.length == 1 and not _.isArray(val2) and val1[0] == val2
      val2 = [val2]

    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    Handlebars.helpers['if'].call(this, not isNone and _.isEqual(val1, val2), options)

  @ne: (val1, val2, values...) ->
    options = values.pop()

    if values
      values.push(val2)
      val2 = _.clone(values).sort()
      if _.isArray(val1)
        # We copy the value to prevent modifying the original
        val1 = _.clone(val1).sort()

    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2)
    Handlebars.helpers['if'].call(this, not isNone and not _.isEqual(val1, val2), options)

  @contains: (array, values...) ->
    options = values.pop()

    isNone = Snakeskin.Util.none(array)
    for value in values
      isNone ||= Snakeskin.Util.none(value)

    contains = false
    if not isNone
      contains = true
      for value in values
        contains &&= value in array

    Handlebars.helpers['if'].call(this, not isNone and contains, options)

  @len: (array, comparator, value, options) ->
    if options == undefined and comparator == undefined
      options = comparator
      comparator = undefined

    if comparator == undefined
      comparator = 'gt'

    if value == undefined
      value = 0

    if not _.isNumber(value)
      value = parseInt(value, 10)

    match = false

    if comparator == 'gt'
      match = array.length > value
    else if comparator == 'gte'
      match = array.length >= value
    else if comparator == 'lt'
      match = array.length < value
    else if comparator == 'lte'
      match = array.length <= value
    else if comparator == 'eq'
      match = array.length == value
    else if comparator == 'ne'
      match = array.length != value

    Handlebars.helpers['if'].call(this, match, options)

  @omits: (array, values...) ->
    options = values.pop()

    isNone = Snakeskin.Util.none(array)
    for value in values
      isNone ||= Snakeskin.Util.none(value)

    omits = false
    if not isNone
      omits = true
      for value in values
        omits &&= value not in array

    Handlebars.helpers['if'].call(this, not isNone and omits, options)

  @between: (val1, val2, val3, options) ->
    isNone = Snakeskin.Util.none(val1) or Snakeskin.Util.none(val2) or Snakeskin.Util.none(val3)
    val2 = Snakeskin.Dates.homogenizeTo(val1, val2)
    val3 = Snakeskin.Dates.homogenizeTo(val1, val3)
    Handlebars.helpers['if'].call(this, not isNone and val2 <= val1 <= val3, options)

  @dateDiff: (value, upper, options) ->
    Snakeskin.Dates.diff(value, upper)

  @dateFormat: (value, format, options) ->
    if format == 'ISO'
      format = '%FT%TZ'
    Snakeskin.Dates.format(value, format, true)

  @split: (values, groups, options) ->
    groups = parseInt(groups, 10)
    perGroup = Math.ceil(values.length / groups)

    output = ''
    for group in [0...groups]
        start = group * perGroup
        end = (group + 1) * perGroup
        splitValues = values[start...end]
        result = options['fn'](splitValues)
        output += result
    new Handlebars.SafeString(output)

  @join: (values, separator, options) ->
    output = (_.escape(value) for value in values).join(separator)
    new Handlebars.SafeString(output)

  @highlight: (string, options) ->
    output = _.escape(string).replace(/\x02/g, '<b>').replace(/\x03/g, '</b>')
    new Handlebars.SafeString(output)

  @wordWrap: (word, options) ->
    word = word.replace(/([a-z])([0-9A-Z])/g, "$1\u200B$2")
    word = word.replace(/([0-9])([A-Z])/g, "$1\u200B$2")
    word = word.replace(/\//, "/\u200B")
    word

  @urlAbbr: (url, domainOnly, options) ->
    openA = '<a href="' + _.escape(url) + '" title="' + _.escape(url) + '">'
    trimmedUrl = url.replace(/^https?:\/\/(www\.)?/, '')
    if domainOnly and options
      trimmedUrl = trimmedUrl.replace(/\/.*$/, '')
    trimmedUrl = _.escape(trimmedUrl)
    trimmedUrl = trimmedUrl.replace('/', "/\u200B")
    closeA = '</a>'
    new Handlebars.SafeString(openA + trimmedUrl + closeA)

  @title: (values...) ->
    # Pop off the options if an object is passed - this allows us to
    # manually call the method in addition to use it as a handlebars helper
    options = values.pop()
    if not _.isObject(options)
      values.push(options)

    values = _.filter(values)
    title = values.join(' - ')
    if title.indexOf('Package Control') == -1
      title += ' - Package Control'
    document.title = title
    ''

  @keyValue: (obj, fn) ->
    output = ''
    for key of obj
      if obj.hasOwnProperty(key)
        output += fn({key: key, value: obj[key]})
    output

  @numAbbr: (value, options) ->
    Snakeskin.Numbers.abbr(value)

  @numFormat: (value, scale, options) ->
    if options == undefined
      options = scale
      scale = 0

    Snakeskin.Numbers.format(value, scale)

  @numOrd: (value, options) ->
    mod = value % 10
    if 10 < value < 14
      suffix = 'th'
    else if mod == 1
      suffix = 'st'
    else if mod == 2
      suffix = 'nd'
    else if mod == 3
      suffix = 'rd'
    else
      suffix = 'th'
    return value.toString() + suffix

  @filesizeAbbr: (value, options) ->
    break_points = [
      [1099511627776.0, 1,       'TB'],
      [1073741824.0,    1,       'GB'],
      [1048576.0,       1,       'MB'],
      [1024.0,          0,       'KB'],
      [1.0,             0,       'B']
    ]

    output = value
    for [divisor, scale, suffix] in break_points
      if value < divisor
        continue
      output = (value / divisor).toFixed(scale) + suffix
      break

    output
