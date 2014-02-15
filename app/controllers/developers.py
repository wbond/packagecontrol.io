from bottle import route, redirect


@route('/docs/developers', name='developers')
def developers_controller():
    redirect('/docs#Package_Developers', 301)
