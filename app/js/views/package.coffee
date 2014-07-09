class App.Views.Package extends Snakeskin.View
  name: 'Package'

  events: {
    'click ul.totals span.key': 'togglePlatform'
  }

  initialize: (options) =>
    @loadScript()

    @placed = false
    @listenTo(@, 'placed', =>
      @$el.find('div#daily_installs').append('<div class="loading">Loading…</div>')
      @$loading = @$('div#daily_installs div.loading')
      @placed = true
      @initializeChart()
    )

    # Ensure redrawing doesn't happen lots of time while dragging
    @_redrawChart = _.debounce(@drawChart, 150)
    $(window).on('resize', @_redrawChart)

  loadScript: ->
    src = '/js/d3.js'
    d3Js = $('script[src="' + src + '"]')
    if d3Js.length == 0
      el = document.createElement('script')
      el.type = 'text/javascript'
      el.src = src
      el.async = false
      el.onload = @initializeChart
      document.body.appendChild(el)

  cleanup: ->
    $(window).off('resize', @_redrawChart)

  initializeChart: =>
    div = @$('#daily_installs')

    # If the HTML isn't there (such as a 404, don't try to initialize)
    if not div.length
      return

    table = div.children('table')

    if window.d3 == undefined or not @placed or @chart
      return

    @$loading.remove()

    @chart = {
      dates:  [],
      data:   [],
      scales: [
        1,
        1,
        1
      ],
      platformMap: {
        windows: 0,
        osx: 1,
        linux: 2
      }
    }

    for th in table.find('tr.dates th')
      @chart.dates.push($(th).text())

    i = 0
    for tr in table.find('tr.platform')
      $tr = $(tr)
      @chart.data[i] = {
        platform: $tr.find('th').text(),
        values: []
      }
      j = 0
      for td in $tr.find('td')
        @chart.data[i].values.push({
          x: j,
          y: parseInt($(td).text()),
          p: i
        })
        j += 1
      i += 1

    #table.remove()

    # Based on http://bl.ocks.org/mbostock/3943967

    @chart.margins = {top: 10, right: 10, bottom: 25, left: 40}
    height = div.innerHeight() - @chart.margins.top - @chart.margins.bottom
    width = div.innerWidth() - @chart.margins.left - @chart.margins.right

    # This takes the raw data and adds .y0 attributes to the values
    # so that it is easy to determine the y offset of the bottom of the
    # stacked rectangles that are going to be created
    @chart.stack = d3.layout.stack().values((d) -> d.values)
    @chart.layeredData = @chart.stack(@chart.data)

    # Determine the maximum stacked value of all three platforms
    yMax = d3.max(@chart.layeredData, (layer) ->
      d3.max(layer.values, (d) -> d.y0 + d.y)
    )
    # Ensure we always have a scale to display
    if yMax < 4
      yMax = 4

    # Create a scale for the x axis
    @chart.xScale = d3.scale.ordinal()
      .domain(d3.range(@chart.dates.length))
      .rangeRoundBands([0, width], 0.08)

    # Create a scale for the y axis
    @chart.yScale = d3.scale.linear()
      .domain([0, yMax])
      .range([height, 0])

    # This creates the primary drawing area (g tag) and uses margins to offset
    @chart.svg = d3.select("#daily_installs")
      .append("svg")
        .attr("height", height + @chart.margins.top + @chart.margins.bottom)
    @chart.stage = @chart.svg
      .append("g")
        .attr("transform", "translate(" + @chart.margins.left + "," + @chart.margins.top + ")")

    # Add the grid before the data rectanges to they show on top
    @chart.stage
      .append("g")
        .attr("class", "y grid")

    # Add the dates to the bottom of the chart
    @chart.stage
      .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")

      # Create a colored layer per platform
    @chart.platformLayers = @chart.stage.selectAll(".layer")
      # Since our data is an array of arrays containing one platform
      # per top-level array, we attach the data to these to get the
      # appropriate data binding at the next level
      .data(@chart.layeredData)

    _chart = @chart
    @chart.platformLayers.enter()
      .append("g")
        .attr("class", (d, i) ->
          platformClass = _chart.data[i].platform.toLowerCase().replace(' ', '')
          "layer " + platformClass
        )
        .attr('height', height)

    # Creates the animation of the rectanges "growing" to full
    # size from left to right
    # Definition of how to display rectangles and their tooltips
    # Add rectangles that pull the actual values from each platform
    @chart.rect = @chart.platformLayers.selectAll("rect").data((d) -> d.values)

    hoverTimeout = null
    @chart.rect.enter()
      .append("rect")
        .attr("x", (d) -> _chart.xScale(d.x))
        .attr("y", -> height)
        .attr("width", -> _chart.xScale.rangeBand())
        .attr("height", 0)
        # Create hover effects that apply to all rectangle in a column
        .on('mouseover', (d, i, p) ->
          if hoverTimeout
            clearTimeout(hoverTimeout)
          platformRects = _chart.rect.select((d) -> @ unless d.p != p)
          platformRects.attr('class', 'hover')
          otherRects = _chart.rect.select((d) -> @ unless d.p == p)
          otherRects.attr('class', 'de-emphasize')
        )
        .on('mouseout', (d, i, p) ->
          hoverTimeout = setTimeout(
            -> _chart.rect.attr('class', ''),
            100
          )
        )
        .append("title")
          .text((d, i) ->
            _chart.dates[i] + "\n  " +
            _chart.data[2].platform + ': ' + Snakeskin.Numbers.format(_chart.data[2].values[i].y) + "\n  " +
            _chart.data[1].platform + ': ' + Snakeskin.Numbers.format(_chart.data[1].values[i].y) + "\n  " +
            _chart.data[0].platform + ': ' + Snakeskin.Numbers.format(_chart.data[0].values[i].y)
          )

    # Generate a grid of lines to make it easy to visually estimate values
    @chart.yGrid = d3.svg.axis()
      .scale(@chart.yScale)
      .ticks(4)
      .orient('left')
      # -width causes the tick to span all the way across the chart,
      # which has the effect of creating a grid
      .tickSize(-width, -width, 0)
      .tickSubdivide(1)
      .tickPadding(9)
      .tickFormat((d, i) -> Snakeskin.Numbers.abbr(d))

    # Setup the ticks at the bottom of the chart showing the dates
    @chart.xAxis = d3.svg.axis()
      .scale(@chart.xScale)
      .tickSize(0, 0, 0)
      .tickPadding(11)
      .tickValues(@chart.dates)
      .orient("bottom")

    @drawChart(null, true)

  drawChart: (e, initial) =>
    div = @$('#daily_installs')
    _chart = @chart

    # If a resize happens before the chart is drawn
    return if not _chart

    # Set up the dimensions of the main drawing area of the chart
    width = div.innerWidth() - @chart.margins.left - @chart.margins.right

    @chart.xScale.rangeRoundBands([0, width], 0.08)
    @chart.svg.attr("width", width + @chart.margins.left + @chart.margins.right)

    if initial
      @chart.rect.transition()
        .delay((d, i) -> i * 10)
        .attr("y", (d) -> _chart.yScale(d.y0 + d.y))
        .attr("height", (d) -> _chart.yScale(d.y0) - _chart.yScale(d.y0 + d.y))

    else
      # When resizing the width, just move the x and change the width
      # but without a transition
      @chart.rect.transition()
        .attr("x", (d) -> _chart.xScale(d.x))
        .attr("width", (d) ->
          _chart.xScale.rangeBand()
        )

    # Resize the grid lines
    @chart.yGrid.tickSize(-width, -width, 0)
    @chart.stage.select('.y.grid').transition().call(@chart.yGrid)

    # Remove ticks as they get too close together
    every = Math.round(45 / (width / 80))
    @chart.xAxis.tickFormat((d, i) -> if (i % every) == 0 then d else '')
    @chart.stage.select('.x.axis').transition().call(@chart.xAxis)

  togglePlatform: (e) =>
    key = $(e.target)
    key.toggleClass('disabled')
    platformName = key.closest('span.installs').attr('class').replace(/\s*installs\s*/, '')
    p = @chart.platformMap[platformName]
    @chart.scales[p] = if @chart.scales[p] == 1 then 0 else 1

    _chart = @chart

    # We do a manual "deep" copy here so we don't mess with the pristine data
    adjustedData = [[], [], []]
    for platformData, p in @chart.data
      adjustedData[p].platform = @chart.data[p].platform
      adjustedData[p].values = []
      for value, d in platformData.values
        adjustedData[p].values[d] = {
          x: value.x,
          # Adjust Y values via the scale to hide platforms
          y: value.y * @chart.scales[p],
          p: value.p
        }

    @chart.platformLayers.data(@chart.stack(adjustedData))
    @chart.rect = @chart.platformLayers.selectAll("rect").data((d) -> d.values)
    @chart.rect.transition()
      .attr("y", (d) -> _chart.yScale(d.y0 + d.y))
      .attr("height", (d) -> _chart.yScale(d.y0) - _chart.yScale(d.y0 + d.y))


