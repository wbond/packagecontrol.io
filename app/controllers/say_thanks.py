from bottle import route, redirect


@route('/say_thanks', name='say_thanks')
def say_thanks_controller():
    redirect('/about', 301)
