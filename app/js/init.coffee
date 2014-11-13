window.App = {
  Views: {}

  # Used to force-reload the app if a user is running
  # an old version of the client-side code.
  version: null

  initialize: (options) ->
    # Allow keyboard shortcuts in inputs
    window.keymaster.filter = ->
      return true
    @router = new App.Router(options)
    @layout = new App.Layout()
    Snakeskin.Helpers.register()
    Snakeskin.View.registerPartials()

    # Even with hashChange: false, backbone converts hashes at the root URL
    # to pushState, which ruins our nice URL, so we stash it and replace it
    if window.location.hash != '' and window.location.pathname == '/'
      window.App.rootHash = window.location.hash
      if history.replaceState
        history.replaceState(null, null, '/')

    Backbone.history.start({pushState: true, hashChange: false})
    if options.statusCode != 200
      @router[@router.errorRoutes[options.statusCode]]()
    @layout.initialized = true
    @router.initialized = true
}
