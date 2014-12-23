class App.Views.Troubleshooting extends Snakeskin.StaticView
  name: 'Troubleshooting'

  initialize: (options) ->
    @listenTo(@, 'placed', =>
      App.popupGallery('ul.screenshots', 'li a')
    )
