Snakeskin.Util.lowerCamel = (string) ->
  string?.replace(
    /(?:_)(\w)/g,
    (_, chr) ->
      if chr then chr.toUpperCase() else ''
  )


Snakeskin.Util.upperCamel = (string) ->
  string?.replace(
    /(?:^|_)(\w)/g,
    (_, chr) ->
      if chr then chr.toUpperCase() else ''
  )


Snakeskin.Util.underscore = (string) ->
  string?.replace(
    /([a-z][A-Z]|[a-zA-Z][0-9]|[0-9][a-zA-Z])/g,
    (chrs) ->
      chrs[0] + '_' + chrs[1]
  ).toLowerCase()


Snakeskin.Util.none = (val) ->
    _.isNull(val) or _.isUndefined(val)
