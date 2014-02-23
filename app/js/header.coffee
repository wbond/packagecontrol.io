class App.Header extends Backbone.View
  el: 'header'

  events: {
    'keyup #search': 'search'
    'focus #search': 'enableShortcuts'
    'blur #search': 'disableShortcuts'
  }

  prevTerms: ''

  initialize: (options) ->
    @layout = options.layout
    @layout.on('change', @highlightNav)
    @$links = @$('nav a')
    @links = ($(a) for a in @$links)
    @$loading = @$('.loading')
    @listenTo(App.router, 'percentage', @animateLoadingBar)

    @$search = @$('#search')
    if @$el
      @prevTerms = @$search.val()
    @search = _.debounce(@_search, 350)
    @listenTo(@, 'placed', =>
      search = @$('input#search').attr('autocomplete', 'off')
    )
    @setupShortcuts()

    $(window).on('popstate', @resetSearch)
    $(window).on('pushstate', @resetSearch)

    if window.navigator.platform.indexOf('Mac') != -1
      keys = @$('span.keys')
      keys.text(keys.text().replace('ctrl', 'cmd'))

    @refreshAd()

  cleanup: =>
    @disableShortcuts()
    key.unbind('enter', 'search')
    key.unbind('up', 'search')
    key.unbind('down', 'search')
    key.unbind('enter')

  isElementInViewport: (el) ->
    rect = el.getBoundingClientRect()

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    )

  _search: (e) =>
    input = $(e.target)
    terms = input.val()

    if @prevTerms == terms
      return

    @prevTerms = terms

    # If the terms are removed when not on the search page, do nothing
    if terms == '' and App.router.path().indexOf('/search') == -1
      return

    route = 'index'
    if terms
      route = 'search'

    url = App.router.url(route, {terms: terms})
    App.router.changeUrl(url)

  resetSearch: =>
    if App.router.path().indexOf('/search') != -1
      terms = App.router.path().replace(/^\/search\/?([^\/]+)?$/, '$1')
      terms = decodeURIComponent(terms)
      @$search.focus()
      @moveCursor(@$search[0])
    else
      terms = ''
      if App.router.path() != '/'
        @$search.blur()
    @$search.val(terms)

  # Focus an input and move the cursor to the last char
  moveCursor: (elem) ->
    elemLen = elem.value.length
    if document.selection
      elem.focus()
      oSel = document.selection.createRange()
      oSel.moveStart('character', -elemLen)
      oSel.moveStart('character', elemLen)
      oSel.moveEnd('character', 0)
      oSel.select()
    else if elem.selectionStart or elem.selectionStart == 0
      elem.selectionStart = elemLen
      elem.selectionEnd = elemLen

  enableShortcuts: =>
    key.setScope('search')

  disableShortcuts: =>
    key.setScope('all')

  setupShortcuts: =>
    # When JS is available, prevent default form action
    key('enter', (e) ->
      e.preventDefault()
    )

    # Allow users to use ctrl+shift+p or cmd+shift+p to focus search
    key('command+shift+p, ctrl+shift+p', (e) =>
      @$search.focus()
    )

    key('enter', 'search', (e) =>
      e.preventDefault()
      if @layout.view.name != 'Search'
        return
      href = @layout.view.$results.find('li.hover a').attr('href')
      App.router.changeUrl(href)
    )

    key('up', 'search', (e) =>
      e.preventDefault()
      if @layout.view.name != 'Search'
        return
      hovered = @layout.view.$results.find('li.hover')
      if hovered.length == 0 or hovered.is(':first-child')
        selected = @layout.view.$results.find('li:last-child')
      else
        selected = hovered.prev()
      hovered.removeClass('hover')
      selected.addClass('hover')
      if not @isElementInViewport(selected[0])
        offset = selected.offset()
        $('html, body').animate({
            scrollTop: offset.top - 20
        }, 150)
    )

    key('down', 'search', (e) =>
      e.preventDefault()
      if @layout.view.name != 'Search'
        return
      hovered = @layout.view.$results.find('li.hover')
      if hovered.length == 0 or hovered.is(':last-child')
        selected = @layout.view.$results.find('li:first-child')
      else
        selected = hovered.next()
      hovered.removeClass('hover')
      selected.addClass('hover')
      if not @isElementInViewport(selected[0])
        offset = selected.offset()
        $('html, body').animate({
            scrollTop: offset.top - 20
        }, 150)
    )

  highlightNav: =>
    @$links.removeClass('active')
    url = App.router.path()
    found = false
    for link in @links
      if url.indexOf(link.attr('href')) == 0
        link.addClass('active')
        found = true
        break
    if not found and url.indexOf('/packages/') == 0
      @$('a[href^="/browse"]').addClass('active')

  animateLoadingBar: (percentage) =>

    dimension = 'height'
    if parseInt(window.innerWidth, 10) <= 600
      dimension = 'width'

    complete = null
    if percentage >= 100
      percentage = 100
      # Turn off CSS transitions when resetting the loading bar
      # so it does not animate shrinking back to 0
      complete = =>
        @$loading.css({
          'transition': 'none',
          '-moz-transition': 'none',
          '-webkit-transition': 'none',
        })
        @$loading.removeData('css-transition')
        @$loading.css(dimension, '0')
      setTimeout(complete, 150)

    # When loading starts, enable the dimension transition
    # for a nice silky smooth loading bar
    if not @$loading.data('css-transition')
      @$loading.css({
        'transition': dimension + ' .15s ease-in-out',
        '-moz-transition': dimension + ' .15s ease-in-out',
        '-webkit-transition': dimension + ' .15s ease-in-out'
      })
      @$loading.data('css-transition', true)

    @$loading.css(dimension, percentage + '%')

  refreshAd: =>
    container = $('#carbonads-container')
    ad_present = container.length > 0

    # Unfortunately the carbonads images seem not to cache and load pretty
    # slow, so to prevent the user from seeing a jarring refresh every time
    # they navigate around the site, the first time we load the ad normally.
    # For every transition after that, we remove the id that adzerk uses to
    # construct the ad content and CSS causes the z-index to increase 1, then
    # we create a new inner div with the id and load the adzerk JS so that
    # it constructs the ad. After one second we remove a CSS class from the old
    # ad to cause it to transition to transparent, showing the new ad behind
    # it. Then finally we remove the old ad, just leaving the new one.
    #
    # I tried a number of different approaches and this was the only one I
    # could find that didn't result in a crappy, jarring page transition for
    # users.
    if ad_present
      oldDiv = container.find('#azcarbon')
      oldDiv.removeAttr('id')
      adDiv = $('<div id="azcarbon"></div>')
      container.find('.carbonad').append(adDiv)
    else
      newContainer = $('<div id="carbonads-container">
        <div class="carbonad"><div id="azcarbon"></div></div>
      </div>')
      $('#nav_container').append(newContainer)
      adDiv = newContainer.find('#azcarbon')

    # There doesn't seem to be a good way to refresh the ad through code
    # since adzerk uses random numbers in the function names. Instead we just
    # remove the old JS and add it again.
    $('script[src^="https://engine.carbonads.com"]').remove()
    script = document.createElement("script")
    script.type = "text/javascript"
    script.async = true
    # We add the number of milliseconds since the epoch to the URL since IE
    # will not re-run a JS file with the same URL as one that has already
    # been loaded on the page previously.
    script.src = "https://engine.carbonads.com/z/58026/azcarbon_2_1_0_VERT?t=" \
      + String(new Date().getTime())
    $('head')[0].appendChild(script)

    adDiv.addClass('loaded')
    if ad_present
      setTimeout((-> oldDiv.removeClass('loaded')), 1000)
      setTimeout((-> oldDiv.remove()), 1200)



