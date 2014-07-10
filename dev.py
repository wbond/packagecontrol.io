#!/usr/bin/env python

import os.path as path

import bottle

import app.env
app.env.name = 'dev'

import app.controllers
from app.lib.json_api_middleware import JsonApiMiddleware
from app.lib.trailing_slash_filter import remove_trailing_slash
from app.lib.version_header import add_version


# For development, serve static files also
app_root = path.join(path.dirname(__file__), 'app')
public_root = path.join(path.dirname(__file__), 'public')


@bottle.route('/<folder:re:(css|img|js|font)>/<filename>')
def server_static(folder, filename):
    return bottle.static_file(filename, root="%s/%s" % (public_root, folder))


@bottle.route('/<filename:re:.*\.html$>')
def server_html(filename):
    response = bottle.static_file(filename, root="%s/html" % app_root)
    # By default the static_file handler creates a new response, so we can't
    # just use the default hook, since it grabs bottle.response
    return add_version(response)


@bottle.route('/favicon.ico')
def server_fav():
    return bottle.static_file('favicon.ico', root=public_root)


sublime_app = bottle.app()
sublime_app = JsonApiMiddleware(sublime_app)

bottle.run(app=sublime_app, host='0.0.0.0', port=9000, debug=True, reloader=True)
