class App.Views.Syncing extends Snakeskin.StaticView
  name: 'Syncing'

  events: {
    'click a.tab': 'changeTab'
  }

  initialize: (options) ->
    @listenTo(@, 'placed', =>
      @st2Tab = @$('a.tab.st2')
      @st3Tab = @$('a.tab.st3')
      @st2Code = @$('pre.st2')
      @st3Code = @$('pre.st3')

      for i of @st2Tab.get()
        @st3Tab.eq(i).after(@st2Tab.eq(i))

      @showSt3()
    )

  showSt2: =>
    @st2Tab.removeClass('inactive')
    @st3Tab.addClass('inactive')
    @st2Code.show()
    @st3Code.hide()

  showSt3: =>
    @st2Tab.addClass('inactive')
    @st3Tab.removeClass('inactive')
    @st2Code.hide()
    @st3Code.show()

  changeTab: (e) =>
    if e.target in @st2Tab.get()
      @showSt2()
    else
      @showSt3()

    e.preventDefault()
