class App.Views.Index extends Snakeskin.View
  name: 'Index'

  title: =>
    Snakeskin.Helpers.title('Package Control', 'the Sublime Text package manager')

  rerender: (name) ->
    @title()

    @$('div.highlights, div.results').remove()
    @$el.append(Handlebars.templates['partials/highlights'](@model))
