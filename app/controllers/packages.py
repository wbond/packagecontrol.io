from bottle import route, redirect


@route('/packages', name='packages')
def packages_controller():
    redirect("/browse", 301)
