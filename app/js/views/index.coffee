class App.Views.Index extends Snakeskin.View
  name: 'Index'

  events: {
    'keyup #search': 'search'
  }

  initialize: (option) ->
    @search = _.throttle(@_search, 500)
    @listenTo(@, 'placed', =>
      @$('input#search').attr('autocomplete', 'off').focus()
    )
    # When JS is available, prevent default form action
    key('enter', (e) ->
      e.preventDefault()
    )

  cleanup: =>
    key.unbind('enter')

  _search: (e) ->
    input = $(e.target)
    url = App.router.url('search', {terms: input.val()})
    App.router.changeUrl(url)

  title: =>
    Snakeskin.Helpers.title('Package Control', 'the Sublime Text package manager')

  rerender: (name) ->
    @title()
    @$('p.intro').slideDown(150)
    
    @$('input#search').val('')
    @$('div.highlights, div.results').remove()
    @$el.append(Handlebars.templates['partials/highlights'](@model))
