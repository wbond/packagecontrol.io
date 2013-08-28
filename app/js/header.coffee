class App.Header extends Backbone.View
  el: 'header'

  initialize: (options) ->
    @layout = options.layout
    @layout.on('change', @highlightNav)
    @$links = @$('nav a')
    @links = ($(a) for a in @$links)
    @$loading = @$('.loading')
    @listenTo(App.router, 'percentage', @animateLoadingBar)

  highlightNav: =>
    @$links.removeClass('active')
    url = App.router.path()
    for link in @links
      if url.indexOf(link.attr('href')) == 0
        link.addClass('active')
        break

  animateLoadingBar: (percentage) =>

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
        @$loading.css({'width': '0'})
      setTimeout(complete, 150)

    # When loading starts, enable the width transition
    # for a nice silky smooth loading bar
    if not @$loading.data('css-transition')
      @$loading.css({
        'transition': 'width .15s ease-in-out',
        '-moz-transition': 'width .15s ease-in-out',
        '-webkit-transition': 'width .15s ease-in-out'
      })
      @$loading.data('css-transition', true)

    @$loading.css({
      'width': percentage + '%'
    })
