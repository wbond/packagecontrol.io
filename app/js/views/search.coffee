class App.Views.Search extends Snakeskin.View
  name: 'Search'

  initialize: (options) ->
    @listenTo(@, 'placed', =>
      @$results = @$('div.results')
    )


  title: =>
    terms = App.router.path().replace(/^.*\/([^\/]+)$/, '$1')
    terms = decodeURIComponent(terms)
    Snakeskin.Helpers.title(terms, 'Search')

  rerender: (name) ->
    @title()

    currentTop = $(document).scrollTop()
    @$('div.highlights, div.results').remove()

    search = $('input#search')
    maxTop = search.offset().top
    @$el.append(Handlebars.templates['partials/results'](@model))

    if currentTop > maxTop + 15
      $(document).scrollTop(0)
