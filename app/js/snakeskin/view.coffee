class window.Snakeskin.View extends Backbone.View
  tagName: 'div'
  id: 'content'

  @registerPartials: ->
    for template of Handlebars.templates
      if template.match(/^partials\//)
        Handlebars.registerPartial(template.replace(/^partials\//, ''), Handlebars.templates[template])

  # Release is for when unbinding a view from an element, but
  # we don't want to actually remove an element from the document
  release: ->
    if @cleanup
      @cleanup()
    @stopListening()
    @undelegateEvents()

  # We allow custom cleanup code to happen in @cleanup()
  remove: ->
    if @cleanup
      @cleanup()
    super

  constructor: (options) ->
    options ||= {}
    @templateName = Snakeskin.Util.underscore(@name)

    # Allow a new view to hook into an existing dom element
    # instead of creating a new one
    if options['exchange']
      options['el'] = $('div#content')
      delete options['exchange']

    super(options)

  render: ->
    template = Handlebars.templates[@templateName]
    @$el.html(template(@model || {}))
    @
