class App.Views.News extends Snakeskin.StaticView
  name: 'News'

  events: {
    'click h2[id]': 'changeHash'
  }

  changeHash: (e) ->
    h2 = $(e.target)
    window.location.hash = '#' + h2.attr('id')
    return false
