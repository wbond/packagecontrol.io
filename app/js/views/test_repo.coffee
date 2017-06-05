class App.Views.TestRepo extends Snakeskin.View
  name: 'TestRepo'

  events: {
    'click button': 'testJson'
  }

  testJson: (e) =>
    e.preventDefault()
    er = $('div.error')
    if er.length > 0
      er.remove()
    json = $('textarea#repo_json').val()
    try
      repo_info = $.parseJSON(json)
      @doRerender({json_string: json, running: true})
      $.ajax({
        url: '/test_repo.json',
        method: 'POST',
        contentType: 'application/json',
        data: json,
        dataType: 'json',
        success: (data, status, xhr) =>
          data.details.num_errors = data.details.errors.length
          data.details.num_warnings = data.details.warnings.length
          @doRerender({result: data, json_string: json})
        error: (xhr, status, error) =>
          @doRerender({error: error, json_string: json})
      })
    catch e
      @doRerender({error: e.message, json_string: json})

  doRerender: (data) =>
    @$el.empty().append(Handlebars.templates['test_repo'](data))
