class App.Views.Search extends Snakeskin.View
  name: 'Search'

  events: {
    'keyup #search': 'search'
    'focus #search': 'enableShortcuts'
    'blur #search': 'disableShortcuts'
  }

  prevTerms: ''

  initialize: (options) ->
    if @$el
      @prevTerms = @$('#search').val()
    @search = _.debounce(@_search, 600)
    @listenTo(@, 'placed', =>
      @$results = @$('div.results')
      search = @$('input#search').attr('autocomplete', 'off')
      search.focus()
      @moveCursor(search[0])
    )
    @setupShortcuts()

  cleanup: =>
    @disableShortcuts()
    key.unbind('enter', 'search')
    key.unbind('up', 'search')
    key.unbind('down', 'search')
    key.unbind('enter')

  title: =>
    Snakeskin.Helpers.title(@prevTerms, 'Search')

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

    key('enter', 'search', (e) =>
      e.preventDefault()
      href = @$results.find('li.hover a').attr('href')
      App.router.changeUrl(href)
    )

    key('up', 'search', (e) =>
      e.preventDefault()
      hovered = @$results.find('li.hover')
      if hovered.length == 0 or hovered.is(':first-child')
        selected = @$results.find('li:last-child')
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
      hovered = @$results.find('li.hover')
      if hovered.length == 0 or hovered.is(':last-child')
        selected = @$results.find('li:first-child')
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

    if not terms
      url = App.router.url('index')
    else
      url = App.router.url('search', {terms: terms})

    @prevTerms = terms
    @title()
    App.router.changeUrl(url)

  rerender: (name) ->
    @title()
    @$('p.intro').slideUp(150)
    
    currentTop = $(document).scrollTop()
    @$('div.highlights, div.results').remove()

    search = @$('input#search')
    if search.length == 0 or not @model
      return

    if @model['terms'] == ''
      search.val(@model['terms'])
    maxTop = search.offset().top
    @$el.append(Handlebars.templates['partials/results'](@model))

    if currentTop > maxTop
      $(document).scrollTop(maxTop - 30)
