class window.Snakeskin.Router extends Backbone.Router
  # If the page has been initialized yet
  initialized: false

  # Info about routes for the sake of generating URLs
  # this is extracted from the app/controllers/ folder.
  routeDefs: {}

  # A list of handlers for HTTP status codes
  errorRoutes: {}

  # Rather than using Backbone.Router.navigate and actually
  # navigating to a new URL before fetching the necessary
  # JSON data, this variable is used to trigger a route
  # handler when a user clicks a local link. Then once the
  # JSON is successfully fetched, Backbone.Router.navigate
  # is used to update the URL in the browser.
  tempFragment: null

  # The current AJAX request happening, for the purpose of cancelling it
  currentXHR: null

  # The constructor requires an option named exportedRoutes that is an object
  # of named route information from bottle.py
  constructor: (options) ->
    Handlebars.registerHelper('url', @_urlHelper)

    # The routes hash that backbone expects
    options = {} unless options?
    options.routes = {}

    for name of options.exportedRoutes
      method = Snakeskin.Util.lowerCamel(name)
      pattern = options.exportedRoutes[name]

      # Skip methods that have not been defined
      if not @[method]
        continue

      @routeDefs[name] = {
        name: name
        pattern: pattern
        method: method
      }

      # Make a backbone compatible pattern
      url = ''
      for piece in pattern
        if piece.type == 'literal'
          url += piece.value
        else
          url += ':' + piece.name
      url = url.replace(/^\//, '')

      options.routes[url] = method

    delete(options.exportedRoutes)
    super(options)

  # Kicks off a change of URL. Runs the handler for the URL before changing
  # it. The handler for a URL should call @ensureData() to perform an ajax
  # request to grab data from the server, or call @finishNavigation() to
  # change the URL in the browser location bar if no server data is needed.
  changeUrl: (href) =>
    if not href
      return false

    if href.indexOf('?') == 0
      href = window.location.pathname + href

    # Remove a single trailing ?
    if href.substr(href.length - 1, 1) == '?'
      href = href.substr(0, href.length - 1)

    if href.indexOf(window.location.origin) == 0
      href = href.replace(window.location.origin, '')

    if history.pushState
      if href.match(/^\//) and @_loadUrl(href)
        return true
    else
      window.location = href

    return false

  # Fetch the .json or .html version of the current router fragment. Once the
  # ajax request completes successfully, trigger the pushState navigation.
  ensureData: (type, success) =>
    if not success?
      success = type
      type = 'json'

    if @tempFragment?
      fragment = @tempFragment
    else
      # Backbone does not actually track the query string in the fragment,
      # however when we have to fall back to the fragment, we can also just
      # grab the query string from window.location due to the fact that
      # the backbone fragment is only used when the URL is changed by a popstate
      # event.
      fragment = Backbone.history.fragment + window.location.search
    _this = @

    # The first time through, don't load the JSON
    # since the HTML will already be present
    if not @initialized
      @initialized = true
      success(null)
      return

    parts = fragment.split('?')
    url = Backbone.history.root + parts[0] + '.' + type
    if parts[1]
      url += '?' + parts[1]

    @currentXHR = $.ajax({
      dataType: type,
      url: url,
      xhr: @_makeXhr,
      success: (data, status, xhr) ->
        _this.checkReloadApp(xhr)
        _this.finishNavigation()
        func = ->
          success(data)
          _this.cleanupNavigation()
        setTimeout(func, 1)

      error: (xhr, status, error) ->
        # If we aborted on purpose, don't run an error handler
        if status == "abort"
          return

        _this.checkReloadApp(xhr)
        _this.finishNavigation()
        route = String(xhr.status)
        if xhr.responseText and type == 'json'
          data = $.parseJSON(xhr.responseText)
        else
          data = xhr.responseText
        if route of _this.errorRoutes
          _this[_this.errorRoutes[route]](data)
        _this.cleanupNavigation()

    })

  # Ensures the client-code is running the same version as the server
  checkReloadApp: (xhr) =>
    if xhr.getResponseHeader('X-App-Version') != App.version
      window.location = @tempFragment

  # Cancels any in-progress AJAX requests
  cancelNavigation: =>
    if @currentXHR
      @currentXHR.abort()
      @currentXHR = null

  # When navigation was performed with @changeUrl(), this method "finishes"
  # the navigation by actually chaning the URL in the browser address bar.
  # The success param is for a consistent interface with @ensureData()
  finishNavigation: (success) =>
    if @tempFragment != null
      # Handle reloads by clearing the fragment
      if Backbone.history.fragment == @tempFragment
        Backbone.history.fragment = null
      @navigate(@tempFragment)
      @tempFragment = null
    @currentXHR = null
    if success
      success()

  # A function that gets run after navigation and a success handler run
  cleanupNavigation: =>

  # Return the current URL
  path: ->
    window.location.pathname + window.location.hash.replace('#', '')

  # Generates a URL based on the route name (from bottle.py)
  # and the provided values
  url: (name, values) =>
    return @_urlHelper(name, {hash: values})

  # Adapted from Backbone.history - used to find a route that matches
  # the URL and invoke it. This is used since we want to only push
  # the URL into the history if the fetch is successful.
  _loadUrl: (url) =>
    # Strip the leading slash
    fragment = url.substring(1)

    _this = @

    _.any(
      Backbone.history.handlers,
      (handler) ->
        if handler.route.test(fragment)
          _this.tempFragment = fragment
          # If there is any current data request in process, cancel it
          # since we are now executing a different URL handler
          _this.cancelNavigation()
          handler.callback(fragment)
          return true
    )

  _makeXhr: =>
    xhr = jQuery.ajaxSettings.xhr()
    xhr.onreadystatechange = @_xhrStateChange
    xhr.addEventListener('progress', @_xhrProgress, false)
    xhr

  # Handlebars.js helper for generating URLs
  _urlHelper: (name, options) =>
    def = @routeDefs[name]

    url = ''
    for piece in def.pattern
      if piece.type == 'literal'
        value = piece.value
      else
        value = encodeURIComponent(options.hash[piece.name])
      url += if value? then value else ''

    return url

  _xhrProgress: (e) =>
    # Fill in the 24 percent between state 3 and 4
    @trigger('percentage', 75 + (e.loaded/e.total) * 24)

  _xhrStateChange: (e) =>
    @trigger('percentage', e.target.readyState * 25)
