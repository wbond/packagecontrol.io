window.App = {
  Views: {}

  initialize: (options) ->
    # Allow keyboard shortcuts in inputs
    key.filter = ->
      return true
    @router = new App.Router(options)
    @layout = new App.Layout()
    Snakeskin.Helpers.register()
    Snakeskin.View.registerPartials()
    Backbone.history.start({pushState: true, hashChange: false})
    if options.statusCode != 200
      @router[@router.errorRoutes[options.statusCode]]()
    @layout.initialized = true
    @router.initialized = true
}
