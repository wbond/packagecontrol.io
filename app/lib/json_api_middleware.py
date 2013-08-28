import re
import json
import datetime

import bottle

from .json_datetime_encoder import JsonDatetimeZEncoder


class JsonApiMiddleware(object):
  def __init__(self, app):
    app.install(bottle.JSONPlugin(json_dumps=lambda s: json.dumps(s, cls=JsonDatetimeZEncoder)))
    self.app = app

  def __call__(self, e, h):
    e['JSON'] = False
    if re.search('\\.json$', e['PATH_INFO']):
        e['PATH_INFO'] = re.sub('\\.json$', '', e['PATH_INFO'])
        e['JSON'] = True

    return self.app(e,h)
