Snakeskin.Numbers.abbr = (num) ->
  break_points = [
    [1000000000000, 2,       'T'],
    [1000000000,    2,       'B'],
    [1000000,       2,       'M'],
    [1000,          0,       'K'],
    [1,             0,       '']
  ]

  output = num
  for [divisor, scale, suffix] in break_points
    if num < divisor
      continue
    output = (num / divisor).toFixed(scale) + suffix
    break

  output


Snakeskin.Numbers.format = (num, scale=0) ->
  num = parseFloat(num).toFixed(scale)

  [int, fraction] = num.split('.')

  suffix = ''
  fraction = fraction?.replace(/0*$/, '')
  if fraction
    suffix = '.' + fraction

  int_parts = []
  while int.length > 3
    cut = int.length - 3
    int_parts.unshift(int[cut..])
    int = int[0...cut]
  if int.length
    int_parts.unshift(int)

  int_parts.join(',') + suffix
