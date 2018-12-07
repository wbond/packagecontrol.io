import os
import re

import glob2
from gears.exceptions import ImproperlyConfigured, FileNotFound
from gears.utils import safe_join

from gears.environment import Environment, DEFAULT_PUBLIC_ASSETS
from gears.finders import FileSystemFinder
from gears_libsass import LibsassCompiler
from gears_coffeescript import CoffeeScriptCompiler
from gears_handlebars import HandlebarsCompiler
from gears_uglifyjs import UglifyJSCompressor
from gears_clean_css import CleanCSSCompressor

from . import env


class ExtFinder(FileSystemFinder):
    """
    Class that finds assets for gears by filtering on extension
    """

    def __init__(self, directories, extensions, ignores):
        # Create a pattern that will only match the specified extensions
        self.ext_pattern = re.compile('|'.join([re.escape(ext) + '$' for ext in extensions]))
        self.ignore_pattern = re.compile('|'.join([re.escape(ignore) + '$' for ignore in ignores]))
        super(ExtFinder, self).__init__(directories)

    def list(self, path):
        for root in self.locations:
            for absolute_path in glob2.iglob(os.path.join(root, path)):
                if os.path.isfile(absolute_path):
                    logical_path = os.path.relpath(absolute_path, root)
                    # Filter out any files that don't end in the specified extensions
                    if not self.ext_pattern.search(absolute_path):
                        continue
                    # Filter out ignored paths
                    if self.ignore_pattern.search(absolute_path):
                        continue
                    yield logical_path, absolute_path


class CustomHandlebarsCompiler(HandlebarsCompiler):
    """
    Handlebars compiler that strips template/ from the name
    """

    def __call__(self, asset):
        asset.attributes.path_without_suffix = asset.attributes.path_without_suffix.replace('templates/', '')
        # Compress whitespace if possible
        if re.search('<pre', asset.processed_source, re.I) is None:
            asset.processed_source = re.sub('[ \t\n]+', ' ', asset.processed_source)
        super(CustomHandlebarsCompiler, self).__call__(asset)


class Assets(object):
    """
    Uses the gears package to compile all .scss and .coffee files into CSS and JS
    """

    def __init__(self):
        project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        app_dir = os.path.join(project_dir, 'app')
        public_dir = os.path.join(project_dir, 'public')

        self.gears = Environment(public_dir, fingerprinting=False,
            manifest_path=False)
        self.gears.finders.register(ExtFinder(
            [app_dir],
            ['.coffee', '.scss', '.handlebars', '.js', '.css'],
            ['app.handlebars', 'partials/header.handlebars', 'partials/footer.handlebars']
        ))

        self.gears.compilers.register('.scss', LibsassCompiler.as_handler())
        self.gears.compilers.register('.coffee', CoffeeScriptCompiler.as_handler())
        self.gears.compilers.register('.handlebars', CustomHandlebarsCompiler.as_handler())

        if env.is_prod():
            self.gears.compressors.register('text/css', CleanCSSCompressor.as_handler())

        self.gears.register_defaults()

    def compile(self):
        """
        Perform the cross-compile of the assets
        """

        self.gears.save()
