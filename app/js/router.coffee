class App.Router extends Snakeskin.Router
  errorRoutes: {
    '404': 'fourOhFour',
    '500': 'fiveHundred'
  }

  index: () =>
    @ensureData((data) =>
      @_parseDates(data, ['trending', 'new', 'top'])
      App.layout.renderExchange('index', data, ['index', 'search'])
    )

  package: (name) =>
    @ensureData((data) =>
      @_parseDates(data)
      App.layout.render('package', data)
    )

  label: (name) ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('label', data)
    )

  labels: (name) ->
    @ensureData((data) =>
      App.layout.render('labels', data)
    )

  browse: () ->
    @ensureData((data) =>
      App.layout.render('browse', data)
    )

  new: () ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('new', data)
    )

  popular: () ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('popular', data)
    )

  trending: () ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('trending', data)
    )

  updated: () ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('updated', data)
    )

  author: (name) ->
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.render('author', data)
    )

  authors: (name) ->
    @ensureData((data) =>
      App.layout.render('authors', data)
    )

  searchBlank: (terms) ->
    @search(terms)

  search: (terms) =>
    @ensureData((data) =>
      @_parseDates(data, 'packages')
      App.layout.renderExchange('search', data, ['index', 'search'])
    )

  stats: =>
    @ensureData((data) =>
      if data
        data['date'] = Snakeskin.Dates.parseISO8601(data['date'])
      App.layout.render('stats', data)
    )

  code: =>
    @ensureData('html', (data) =>
      App.layout.render('code', data)
    )

  docs: =>
    @ensureData('html', (data) =>
      App.layout.render('docs', data)
    )

  developers: =>
    @ensureData('html', (data) =>
      App.layout.render('developers', data)
    )

  news: =>
    @ensureData('html', (data) =>
      App.layout.render('news', data)
    )

  installation: =>
    @ensureData('html', (data) =>
      App.layout.render('installation', data)
    )

  issues: =>
    @ensureData('html', (data) =>
      App.layout.render('issues', data)
    )

  sayThanks: =>
    @ensureData('html', (data) =>
      App.layout.render('say_thanks', data)
    )

  settings: =>
    @ensureData('html', (data) =>
      App.layout.render('settings', data)
    )

  styles: =>
    @ensureData('html', (data) =>
      App.layout.render('styles', data)
    )

  syncing: =>
    @ensureData('html', (data) =>
      App.layout.render('syncing', data)
    )

  usage: =>
    @ensureData('html', (data) =>
      App.layout.render('usage', data)
    )

  fourOhFour: (data) ->
    App.layout.render('four_oh_four', data)

  fiveHundred: (data) ->
    App.layout.render('five_hundred', data)

  cleanupNavigation: =>
    window._gaq.push(['_trackPageview'])


  _parseDates: (obj, keys) ->
    if not obj
      return

    if _.isArray(keys)
      array = _.flatten([obj[key] for key in keys])
    else if keys
      array = obj[keys]
    else
      array = [obj]

    for value in array
      for field in ['first_seen', 'last_seen', 'last_modified']
        if value[field]
          value[field] = Snakeskin.Dates.parseISO8601(value[field])
