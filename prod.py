import sys
import os

import bottle
import rollbar
import webob

import app.env
app.env.name = 'prod'

import app.controllers
from app.lib.json_api_middleware import JsonApiMiddleware
from app.lib.trailing_slash_filter import remove_trailing_slash
from app.lib.version_header import add_version
from app import config


rollbar.init(config.read_secret('rollbar_key'), 'production', code_version=app.env.sha1)


def application(environ, start_response):
    try:
        application = bottle.app()
        application.catchall = False
        application = JsonApiMiddleware(application)
        return application(environ, start_response)

    except:
        rollbar.report_exc_info(sys.exc_info(), webob.Request(environ))

        # Bare bones 500 handler
        content = b''
        if environ.get('JSON'):
            content = '{"__status_code__": 500}'
            content_type = 'application/json; charset=UTF-8'
        else:
            dirname = os.path.dirname(__file__)
            five_hundred_path = os.path.join(dirname, 'app/html/five_hundred.html')
            with open(five_hundred_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content_type = 'text/html; charset=UTF-8'
        content = content.encode('utf-8')
        start_response(
            '500 Internal Server Error',
            [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content)))
            ],
            sys.exc_info()
        )
        environ['wsgi.errors'] = content
        return [content]
