class App.Views.Installation extends Snakeskin.StaticView
  name: 'Installation'

  events: {
    'click a.tab': 'changeTab'
  }

  initialize: (options) ->
    @listenTo(@, 'placed', =>
      @st2Tab = @$('a.tab.st2')
      @st3Tab = @$('a.tab.st3')
      @st2Code = @$('p.code.st2')
      @st3Code = @$('p.code.st3')
      
      @st3Tab.after(@st2Tab)
      hashChange = (initial) =>
        hash = window.location.hash
        if hash == '#st2'
          @showSt2()
        else if hash == '#st3' or (initial and hash == '')
          @showSt3()

      window.onhashchange = hashChange
      hashChange(true)
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
    if e.target == @st2Tab[0]
      @showSt2()
      window.location.hash = '#st2'
    else
      @showSt3()
      window.location.hash = '#st3'

    e.preventDefault()
