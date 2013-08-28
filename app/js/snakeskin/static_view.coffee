class window.Snakeskin.StaticView extends Snakeskin.View
  render: =>
    html = @model

    match = html.match(/<title>(.*?)<\/title>/i)
    if match
      html = html.replace(match[0], '')
      Snakeskin.Helpers.title(_.unescape(match[1]))

    @$el.html(html)
    @
