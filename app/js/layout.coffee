class App.Layout extends Backbone.View
  el: 'body'

  events: {
    'click a': 'handleClick'
    'click h2[id]': 'setHash'
    'click h3[id]': 'setHash'
    'click h4[id]': 'setHash'
    'click h5[id]': 'setHash'
    'click #notification': 'hideNotification'
  }

  view: null

  initialized: false

  scrollPositions: []
  lastScrollPosition: null

  initialize: (options) ->
    $(window).on('pushstate', @saveScroll)
    $(window).on('popstate', @restoreScroll)
    @header = new App.Header({layout: @})

  saveScroll: =>
    @scrollPositions.push($(window).scrollTop())

  restoreScroll: =>
    previous = @scrollPositions.pop()
    if previous?
      @lastScrollPosition = previous

  changeView: (class_name, class_, data) =>
    # We track the class to remove and do it right after adding the new
    # class in order to prevent flashing of styles
    removeClass = null

    # If there is no view right now and initlization is completed, then
    # no view was ever attached to the existing DOM, so we need to attach
    # something to it so we can move it out of the way for the new view
    if @initialized and not @view
      @view = new Snakeskin.View({el: '#content'})

    # If there was previously a view, we need to create
    # a new view, render it and swap out the old
    if @view
      newView = new class_({model: data})

      newView.render()

      if @view.templateName and @view.templateName != newView.templateName
        removeClass = @view.templateName

      @view.$el.removeAttr('id')
      newView.$el.insertAfter(@view.$el)

      # Ensure the Backbone.View cleanup happens
      @view.remove()

    # If there was not a view, we just need to attach
    # to the existing HTML that is there
    else
      newView = new class_({el: '#content', model: data})

    @$el.addClass(newView.templateName)
    if removeClass
      @$el.removeClass(removeClass)
    newView.trigger('placed')

    @view = newView

    if @lastScrollPosition
      destScroll = @lastScrollPosition
      @lastScrollPosition = null
    else
      destScroll = 0

    if not _.isFunction(window.scrollTo)
      @notify('
        You have "Better Pop Up Blocker" installed, however it removes certain
        Javascript functionality used by this site. Please open the options
        and uncheck "Automatically moving & resizing windows" under
        "Blocked Functions".
      ')
    else
      $(window).scrollTop(destScroll)

  notify: (message) =>
    @hideNotification()
    html = Handlebars.templates['partials/notification']({
      message: message
    })
    @$el.append(html)

  hideNotification: =>
    @$('#notification').remove()

  # If the oldView is the name of the current view, don't
  # do a full re-render, but swap out the view objects
  exchangeViewIf: (class_name, class_, data, oldView) =>
    # We track the class to remove and do it right after adding the new
    # class in order to prevent flashing of styles
    removeClass = null

    if _.isString(oldView)
      oldView = [oldView]

    if not @view or @view.templateName not in oldView
      return @changeView(class_name, class_, data)

    templateName = Snakeskin.Util.underscore(class_name)
    if @view.templateName != templateName
      @view.release()

      if @view.templateName
        removeClass = @view.templateName

      newView = new class_({model: data, exchange: true})

      newView.rerender(@view.templateName)

      @$el.addClass(newView.templateName)
      if removeClass
        @$el.removeClass(removeClass)
      @view = newView

    else
      @view.model = data
      @view.rerender(@view.templateName)

    @view.trigger('placed')

  isView: (name) ->
    @$el.hasClass(name)

  render: (name, data={}) ->
    class_name = Snakeskin.Util.upperCamel(name)
    class_ = App.Views[class_name]

    @changeView(class_name, class_, data)
    @trigger('change')

  renderExchange: (name, data, oldView) ->
    class_name = Snakeskin.Util.upperCamel(name)
    class_ = App.Views[class_name]

    @exchangeViewIf(class_name, class_, data, oldView)
    @trigger('change')

  setTitle: (title) ->
    if title.indexOf('Package Control') == -1
      title += ' - Package Control'
    document.title = title

  handleClick: (e) ->
    # Allow browser default when a modified is pressed
    if e.altKey or e.shiftKey or e.ctrlKey or e.metaKey
      return

    link = $(e.target)
    if not link.is('a')
      link = link.closest('a')
    href = link.attr('href')
    if App.router.changeUrl(href)
      e.preventDefault()
      e.stopPropagation()

  setHash: (e) ->
    heading = $(e.target)
    window.location.hash = '#' + heading.attr('id')
