class App.Views.Index extends Snakeskin.View
  name: 'Index'

  title: =>
    Snakeskin.Helpers.title('Package Control', 'the Sublime Text package manager')

  initialize: (options) =>
    @listenTo(@, 'placed', =>
      if window.App.rootHash == '#discover'
        $('#search').focus()
    )

    # If a browser doesn't support websockets (IE9, Android 2) then no charts
    if typeof window.WebSocket != "undefined"
      src = '/js/d3.js'
      d3Js = $('script[src="' + src + '"]')
      if d3Js.length == 0
        el = document.createElement('script')
        el.type = 'text/javascript'
        el.src = src
        el.async = false
        el.onload = @initializeStats
        document.body.appendChild(el)

      @listenTo(@, 'placed', =>
        @initializeStats()
      )

      @chart = {}
      @socketConfig = {}

  cleanup: =>
    if @chart
      @stopWebsocket()
      $('#realtime').remove()
      $(document).off(@visibilityChange, @handleVisibility)
      $(window).off('resize', @_redrawChart)

  rerender: (name) ->
    @title()

    @$('div.highlights, div.results').remove()
    @$el.append(Handlebars.templates['partials/highlights'](@model))

  handleVisibility: =>
    if document[@hiddenAttr]
      $('#realtime .paused').fadeIn()
      @stopWebsocket()
    else
      @startWebsocket()

  initializeStats: =>
    # Make sure our prerequisites are available
    if not @$el.is(':visible') or not window.d3
      return

    if typeof document.hidden != "undefined"
      @hiddenAttr = "hidden"
      @visibilityChange = "visibilitychange"
    else if typeof document.mozHidden != "undefined"
      @hiddenAttr = "mozHidden"
      @visibilityChange = "mozvisibilitychange"
    else if typeof document.msHidden != "undefined"
      @hiddenAttr = "msHidden"
      @visibilityChange = "msvisibilitychange"
    else if typeof document.webkitHidden != "undefined"
      @hiddenAttr = "webkitHidden"
      @visibilityChange = "webkitvisibilitychange"
    $(document).on(@visibilityChange, @handleVisibility)

    @_redrawChart = _.debounce(@drawChart, 250)
    $(window).on('resize', @_redrawChart)

    @buildChart()
    @configureWebsocket()

  configureWebsocket: =>
    data = {
      channel: [],
      web: [],
      usage: []
    }

    _socketConfig = {
      # These are JS timeouts, aka scheduling
      interval: null,
      timeoutTimeout: null,
      sendTimeout: null,

      generation: 0,
      socket: null,
      # This is the number of seconds we wait for data
      socketTimeout: 10,
      backoff: 2000,

      onopen: null,
      onerror: null,
      onmessage: null,
      onclose: null,

      lastStep: null
    }

    _chart = @chart

    # Make these available as local variables for the sake of the closures
    # so that we don't have to bind the websocket event handlers to "this"
    startWebsocket = @startWebsocket
    advanceChart = @advanceChart

    _socketConfig.send = (message) ->
      if not _socketConfig.socket
        return
      if _socketConfig.socket.readyState != 1
        return
      _socketConfig.socket.send(message)

    # Set up event handlers for the various websocket events
    _socketConfig.onopen = ->
      _socketConfig.send("full")

    _socketConfig.onclose = ->
      # We don't currently do anything on close

    _socketConfig.onerror = (e) ->
      if _socketConfig.timeoutTimeout
        clearTimeout(_socketConfig.timeoutTimeout)
        _socketConfig.timeoutTimeout = null

      if _socketConfig.sendTimeout
        clearTimeout(_socketConfig.sendTimeout)
        _socketConfig.sendTimeout = null

      # If a bunch of errors happen, reduce the frequency at
      # which we try to reconenct to the websockets server
      if _socketConfig.generation > 4
        _socketConfig.backoff = 5000

      _socketConfig.socket = null
      setTimeout(startWebsocket, _socketConfig.backoff)

    _socketConfig.onmessage = (e) ->
      # If we get a response, discard out home-made connection timeout handler
      if _socketConfig.timeoutTimeout
        clearTimeout(_socketConfig.timeoutTimeout)
        _socketConfig.timeoutTimeout = null

      res = JSON.parse(e.data)

      # Skip the data in the response that we already have
      while _socketConfig.lastStep and res.begin <= _socketConfig.lastStep
        res.channel.shift()
        res.usage.shift()
        res.web.shift()
        res.begin += res.step

      # Push the new counts onto the data stack in
      # the format that our d3 code is expecting it
      time = res.begin
      while res.channel.length > 0
        data.channel.push({
          x: time,
          y: res.channel.shift(),
          t: 0
        })
        data.web.push({
          x: time,
          y: res.web.shift(),
          t: 1
        })
        data.usage.push({
          x: time,
          y: res.usage.shift(),
          t: 2
        })
        time += res.step

      # Make sure we don't build up too much data
      if data.channel.length > 63
        data.channel = data.channel.slice(-63)
        data.web = data.web.slice(-63)
        data.usage = data.usage.slice(-63)

      _socketConfig.lastStep = res.end

      if _socketConfig.interval == null
        # If we are reconnecting, we always do a full refresh of the chart
        _chart.intervalsToProcess = _chart.maxEntries - 1
        advanceChart(data)

        # This interval is responsible to making sure the chart is updated
        # with new data with the same frequency as the data (the "step" values)
        # and not how often a websocket frame is received
        _socketConfig.interval = setInterval(
          (->
            advanceChart(data)
          ),
          res.step * 1000
        )

      # Queue the request for the next chunk of data
      _socketConfig.sendTimeout = setTimeout(
        (->
          _socketConfig.send("since:" + String(_socketConfig.lastStep))

          # If the websocket does not receive a response, we abandon the socket,
          # which is a homegrown approach to a socket timeout since websockets
          # don't seem to make that functionality available.

          # Create local reference for the timeoutTimeout
          socket = _socketConfig.socket
          _socketConfig.timeoutTimeout = setTimeout(
            (->
              return if not socket
              # Clear the global socket config
              socket.onerror?()
              # Clear the event handlers on this socket in case a
              # response ever comes through
              socket.onopen = null
              socket.onerror = null
              socket.onclose = null
              socket.onmessage = null
            ),
            _socketConfig.socketTimeout * 1000
          )
        ),
        # The res.step is the number of seconds a chunk of data is for, so here
        # we wait for 2 more steps to accumulate before we ask for more data
        res.step * 2 * 1000
      )

    @socketConfig = _socketConfig
    @startWebsocket()

  startWebsocket: =>
    _socketConfig = @socketConfig
    _socketConfig.generation += 1

    ws = new WebSocket('wss://' + window.location.hostname + '/realtime')
    ws.onopen = _socketConfig.onopen
    ws.onerror = _socketConfig.onerror
    ws.onmessage = _socketConfig.onmessage
    ws.onclose = _socketConfig.onclose

    _socketConfig.socket = ws

  stopWebsocket: =>
    _socketConfig = @socketConfig

    if _socketConfig.interval
      clearInterval(_socketConfig.interval)
      _socketConfig.interval = null

    if _socketConfig.timeoutTimeout
      clearTimeout(_socketConfig.timeoutTimeout)
      _socketConfig.timeoutTimeout = null

    if _socketConfig.sendTimeout
      clearTimeout(_socketConfig.sendTimeout)
      _socketConfig.sendTimeout = null

    if _socketConfig.socket
      socket = _socketConfig.socket
      _socketConfig.socket = null
      socket.onopen = null
      socket.onmessage = null
      socket.onerror = null
      socket.onclose = null
      socket.close()

    _socketConfig.lastStep = null

  buildChart: () =>
    div = $(Handlebars.templates['partials/realtime']())
    torso = $('#torso')
    torso.append(div)

    _chart = {
      inited: true,
      data:   [
        {
          type: 'channel',
          values: []
        },
        {
          type: 'web',
          values: []
        },
        {
          type: 'usage',
          values: []
        }
      ],
      scales: [
        1,
        1,
        1
      ],
      typeMap: {
        channel: 0,
        web: 1,
        usage: 2
      },
      yMax: 0,
      maxEntries: 60,
      begin: null,
      # Track how many internal to process when updating the chart.
      # This will normally be 1, but could be more if the websocket
      # times out.
      intervalsToProcess: 0,
      intervalsProcessed: 0
    }
    @chart = _chart

    _chart.xCallback = (d, i) ->
      _chart.xScale((d.x - _chart.begin)/2)

    _chart.yCallback = (d) ->
      _chart.yScale(d.y0 + d.y)

    _chart.heightCallback = (d) ->
      _chart.yScale(d.y0) - _chart.yScale(d.y0 + d.y)

    _chart.widthCallback = (d) ->
      _chart.xScale.rangeBand()

    _chart.titleCallback = (d, i) ->
      return _chart.data[2].type + ': ' + _chart.data[2].values[i].y + "\n" +
        _chart.data[1].type + ': ' + _chart.data[1].values[i].y + "\n" +
        _chart.data[0].type + ': ' + _chart.data[0].values[i].y

    # Based on http://bl.ocks.org/mbostock/3943967

    _chart.margins = {top: 8, right: 30, bottom: 0, left: 0}
    _chart.height = 90
    _chart.width = @$el.innerWidth() - _chart.margins.left - _chart.margins.right
    _chart.width = Math.floor(_chart.width / 60) * 60

    # This takes the raw data and adds .y0 attributes to the values
    # so that it is easy to determine the y offset of the bottom of the
    # stacked rectangles that are going to be created
    _chart.stack = d3.layout.stack().values((d) -> d.values)
    _chart.layeredData = _chart.stack(_chart.data)

    # This creates the primary drawing area (g tag) and uses margins to offset
    _chart.svg = d3.select("#realtime")
      .append("svg")
        .attr("height", _chart.height + _chart.margins.top + _chart.margins.bottom)
    _chart.stage = _chart.svg
      .append("g")
        .attr("transform", "translate(" + _chart.margins.left + "," + _chart.margins.top + ")")

    # Add the grid before the data rectanges to they show on top
    _chart.stage
      .append("g")
        .attr("class", "y grid")
          .attr("transform", "translate(" + (_chart.width + 4) + ",0)")

    _chart.stage
      .append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + _chart.height + ")")

    # Create a colored layer per type
    _chart.typeLayers = _chart.stage.selectAll(".layer")
      # Since our data is an array of arrays containing one type
      # per top-level array, we attach the data to these to get the
      # appropriate data binding at the next level
      .data(
        _chart.layeredData,
        (l) -> l.type
      )

    _chart.typeLayers.enter()
      .append("g")
        .attr("class", (d, i) ->
          typeClass = _chart.data[i].type.toLowerCase().replace(' ', '')
          "layer " + typeClass
        )
        .attr('height', _chart.height)

    # Creates the animation of the rectanges "growing" to full
    # size from left to right
    # Definition of how to display rectangles and their tooltips
    # Add rectangles that pull the actual values from each type
    _chart.rect = _chart.typeLayers.selectAll("rect").data(
      (l) -> l.values,
      (d) -> d.x
    )


    @adjustYScale()

    # Create a scale for the x axis
    _chart.xScale = d3.scale.ordinal()
      .domain(d3.range(_chart.maxEntries))
      .rangeRoundBands([0, _chart.width], 0.08, 0)

    _chart.rect.enter()
      .append("rect")
        # We use timestamps for the x component of the data, but then
        # use the begin time of the data to calculate the x display postition
        .attr("x", _chart.xCallback)
        .attr("width", _chart.widthCallback)
        .attr("y", _chart.height)
        .attr("height", 0)
        .append("title").text(_chart.titleCallback)
    _chart.rect.exit().remove()

    @drawChart(null, true)

  adjustYScale: (forceAdjust) =>
    _chart = @chart

    # Determine the maximum stacked value of all three platforms
    yMax = d3.max(_chart.layeredData, (layer) ->
      d3.max(layer.values, (d) -> d.y0 + d.y)
    )
    # Ensure we always have a scale to display
    if not yMax or yMax < 10
      yMax = 10

    adjust = yMax > _chart.yMax
    _chart.yMax = yMax

    if adjust or forceAdjust
      _chart.yScale = d3.scale.linear()
        .domain([0, yMax])
        .range([_chart.height, 0])

      # Generate a grid of lines to make it easy to visually estimate values
      _chart.yGrid = d3.svg.axis()
        .scale(_chart.yScale)
        .ticks(3)
        .orient('right')
        # -width causes the tick to span all the way across the chart,
        # which has the effect of creating a grid
        .tickSize(-(_chart.width + 4), -(_chart.width + 4), 0)
        .tickSubdivide(0)
        .tickPadding(5)
        # Hide the tick for 0
        .tickFormat((d, i) -> if d == 0 then '' else d)

      # Resize the grid lines
      _chart.stage.select('.y.grid').transition().call(_chart.yGrid)
      return true

    return false

  drawChart: (e, initial) =>
    _chart = @chart

    # Set up the dimensions of the main drawing area of the chart
    _chart.width = @$el.innerWidth() - _chart.margins.left - _chart.margins.right
    _chart.width = Math.floor(_chart.width / 60) * 60

    _chart.xScale = d3.scale.ordinal()
      .domain(d3.range(_chart.maxEntries))
      .rangeRoundBands([0, _chart.width], 0.08, 0)

    calcWidth = _chart.width + _chart.margins.left + _chart.margins.right
    _chart.svg.attr("width", calcWidth)
    $('#realtime .no_data').width(calcWidth)
    $('#realtime .paused').width(calcWidth)

    # We don't use transitions for the follow changes because it may conflict
    # with the transition of the periodic data updates, leading to dropped bars
    _chart.typeLayers.selectAll('rect')
      .attr("x", _chart.xCallback)
      .attr("width", _chart.widthCallback)

    _chart.yGrid.tickSize(-(_chart.width + 4), -(_chart.width + 4), 0)
    _chart.stage.select('.y.grid')
      .call(_chart.yGrid)
      .attr("transform", "translate(" + (_chart.width + 4) + ",0)")

  advanceChart: (data) =>
    _chart = @chart
    _chart.intervalsToProcess += 1

    noData = $('#realtime .no_data')
    paused = $('#realtime .paused')

    # If there is no data, queue a bunch of operations
    if data['channel'].length == 0
      noData.fadeIn()
      return

    # If we didn't have data before, now hide the message
    if noData.is(':visible')
      noData.fadeOut()

    if paused.is(':visible')
      paused.fadeOut()

    elementsToChange = 0

    # If we queued up a huge bunch of intervals to process, we don't ever want
    # to handle more than the max number of entries in the chart
    if _chart.intervalsToProcess > _chart.maxEntries
      _chart.intervalsToProcess = _chart.maxEntries

    # Update the chart data with the data queue passed into the method
    while data['channel'].length > 0 and _chart.intervalsToProcess > 0
      for type in ['web', 'channel', 'usage']
        typeNum =  _chart.typeMap[type]
        # Remove the oldest data entry
        if _chart.data[typeNum].values.length >= _chart.maxEntries
          _chart.data[typeNum].values.shift()
        # Add the new one
        _chart.data[typeNum].values.push(data[type].shift())
      _chart.intervalsToProcess -= 1
      elementsToChange += 1

    if elementsToChange == 1
      _chart.intervalsProcessed += 1
    else
      _chart.intervalsProcessed = elementsToChange

    _chart.begin = _chart.data[0].values[0].x

    _chart.layeredData = _chart.stack(_chart.data)

    # If we are doing a bulk update, or every handful of requests, recalculate
    # the yscale for a better veritcal fit of the chart
    adjusted = @adjustYScale(elementsToChange > 1 or _chart.intervalsProcessed % 10 == 0)

    #_chart.rect = _chart.typeLayers.selectAll("rect").data((d) -> d.values)
    res = _chart.typeLayers.data(_chart.layeredData).selectAll('rect').data(
      (d) -> d.values,
      (d) -> d.x
    )

    if elementsToChange == 1
      @advanceSingle(res, adjusted)
    else
      @advanceMultiple(res)

  advanceSingle: (res, yScaleAdjusted) =>
    _chart = @chart

    # Persisting rectangles
    persisting = res.transition()
      # Ensures the gap between the columns doesn't collapse due to easing
      .delay(10)
      .attr("x", _chart.xCallback)

    # If the y scale was adjusted due to a new larger value,
    # adjust all of the values down to the fit the new scale
    if yScaleAdjusted
      persisting.attr("y", _chart.yCallback)
        .attr("height", _chart.heightCallback)

    # Old rectangle
    res.exit()
      .transition().attr('width', 0)
      .remove()

    # New rectangle
    newRect = res.enter()
      .append("rect")
        .attr("x", _chart.xCallback)
        .attr("width", _chart.widthCallback)
        .attr("y", _chart.height)
        .attr("height", 0)
    newRect.append("title").text(_chart.titleCallback)
    newRect.transition()
      .delay(500)
      .attr("y", _chart.yCallback)
      .attr("height", _chart.heightCallback)

  advanceMultiple: (res) =>
    _chart = @chart

    # When there is a batch update, we hide everything
    # then animate it all back in for a smoother look

    # Shrink the old data, then remove
    res.exit().transition()
      .delay((d, i) -> i * 10)
      .duration(150)
      .attr("y", _chart.height)
      .attr("height", 0)
      .remove()

    # Shrink all persisting data
    res.transition()
      .delay((d, i) -> i * 10)
      .duration(150)
      .attr("y", _chart.height)
      .attr("height", 0)
    # Then move it to the correct new position
    trans = res.transition()
      .delay((d, i) -> 150 + i * 10)
      .duration(10)
      .attr("x", _chart.xCallback)
    # Finally, animate it back to proper height
    trans.transition()
      .delay((d, i) -> 160 + i * 10)
      .duration(150)
      .attr("y", _chart.yCallback)
      .attr("height", _chart.heightCallback)

    # Create the new bars
    newRect = res.enter()
      .append("rect")
        .attr("x", _chart.xCallback)
        .attr("width", _chart.widthCallback)
        .attr("y", _chart.height)
        .attr("height", 0)
    newRect.append("title").text(_chart.titleCallback)
    # And animate their height in series with the persisting data
    newRect.transition()
      .delay((d, i) -> 160 + i * 10)
      .attr("y", _chart.yCallback)
      .attr("height", _chart.heightCallback)


