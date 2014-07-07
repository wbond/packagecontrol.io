import os
import re
import time
import sass
import sys
import traceback
import gears
import argparse

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import app.env

parser = argparse.ArgumentParser(description='Compile the JS and CSS')
parser.add_argument('env', nargs='?', default='dev')

args = parser.parse_args()
app.env.name = args.env

from app.assets import Assets

path = os.getcwd()
assets = Assets()

def compile_assets():
    start = time.time()
    try:
        assets.compile()
        end = time.time()
        print('done (%f seconds)' % (end - start))
    except (sass.CompileError) as e:
        end = time.time()
        print('errror (%f seconds)' % (end - start))
        out = "  " + traceback.format_exc().replace("\n", "\n  ")
        out = out.replace("\"%s" % path, '".')
        print(out)
    except (gears.asset_handler.AssetHandlerError) as e:
        end = time.time()
        out = str(e.args[0], encoding='utf-8').replace("\n", "\n  ")
        out = out.replace("%s" % path, '.')
        print(out)
    return end

def update_version():
    with open('./app/js/version.coffee', 'w') as f:
        app.env.reload() # Make sure was have the up-to-date version
        f.write("window.App.version = '%s'" % app.env.version)

print('Initial compilation of assets ... ', end='')
update_version()
compile_assets()
if app.env.name == 'prod':
    sys.exit(0)


class PathChangeHandler(PatternMatchingEventHandler):
    last_run = None

    def on_any_event(self, event):
        if self.last_run and self.last_run > time.time() - 0.01:
            # Prevent random duplicate events with inotify
            return
        print(u'Compiling assets ... ', end='')
        self.last_run = compile_assets()


class VersionChangeHandler(PatternMatchingEventHandler):
    def on_any_event(self, event):
        update_version()


asset_handler = PathChangeHandler(patterns=['*.coffee', '*.scss', '*.handlebars', '*.js'])
version_handler = VersionChangeHandler(patterns=['*/version.yml'])

observer = Observer()
observer.start()
observer.schedule(asset_handler, path='./app/', recursive=True)
observer.schedule(version_handler, path='./', recursive=False)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
