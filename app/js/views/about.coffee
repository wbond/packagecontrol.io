class App.Views.About extends Snakeskin.StaticView
  name: 'About'

  events:
    'click #buy_beer': 'handlePayPal'

  initialize: (options) ->
    if @$el
      @prevTerms = @$('#search').val()
    @search = _.throttle(@_search, 500)
    @listenTo(@, 'placed', @setupJS)

  setupJS: =>
    paypal = @$('form.paypal')[0]
    content = @$('div.options')[0]

    gps = @scriptTag()
    gps.src = 'https://grtp.co/v1.js'
    gps.setAttribute('data-gratipay-username','wbond')
    content.appendChild(gps)

  scriptTag: ->
    el = document.createElement('script')
    el.type = 'text/javascript'
    el.async = true
    el

  handlePayPal: ->
    button = @$('#buy_beer')
    button.closest('form').click(->
        $(@).submit()
        return false
    )
