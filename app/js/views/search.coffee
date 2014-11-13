class App.Views.Search extends Snakeskin.View
  name: 'Search'

  initialize: (options) ->
    @listenTo(@, 'placed', =>
      input = $('#search')
      input.focus()
      # Everything but IE supports setSelectionRange
      if input[0].setSelectionRange
        length = input.val().length * 2
        input[0].setSelectionRange(length, length)
      # IE sets the cursor to the end if you set the value to its previous value
      else
        input.val(input.val())

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
