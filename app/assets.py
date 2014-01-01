import os
import re

from gears.exceptions import ImproperlyConfigured, FileNotFound
from gears.utils import safe_join, listdir

from gears.environment import Environment, DEFAULT_PUBLIC_ASSETS
from gears.finders import FileSystemFinder
from gears_scss import SCSSCompiler
from gears_coffeescript import CoffeeScriptCompiler
from gears_handlebars import HandlebarsCompiler
from gears_uglifyjs import UglifyJSCompressor
from gears_clean_css import CleanCSSCompressor

from . import env


class ExtFinder(FileSystemFinder):
    """
    Class that finds assets for gears by filtering on extension
    """

    def __init__(self, directories, extensions):
        # Create a pattern that will only match the specified extensions
        self.ext_pattern = re.compile('|'.join([re.escape(ext) + '$' for ext in extensions]))
        super(ExtFinder, self).__init__(directories)

    def list(self, path, recursive=False):
        for root in self.locations:
            matched_path = self.find_location(root, path)
            if not matched_path or not os.path.isdir(matched_path):
                continue
            for filepath in listdir(matched_path, recursive=recursive):
                # Filter out any files that don't end in the specified extensions
                if not self.ext_pattern.search(filepath):
                    continue

                absolute_path = os.path.join(matched_path, filepath)
                logical_path = os.path.join(path, filepath)
                if os.path.isfile(absolute_path):
                    yield logical_path, absolute_path


class CustomHandlebarsCompiler(HandlebarsCompiler):
    """
    Handlebars compiler that strips template/ from the name
    """

    def __call__(self, asset):
        asset.attributes.path_without_suffix = asset.attributes.path_without_suffix.replace('templates/', '')
        super(CustomHandlebarsCompiler, self).__call__(asset)


class Assets(object):
    """
    Uses the gears package to compile all .scss and .coffee files into CSS and JS
    """

    def __init__(self):
        project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        app_dir = os.path.join(project_dir, 'app')
        public_dir = os.path.join(project_dir, 'public')

        self.gears = Environment(public_dir, public_assets=[self._public_assets],
            fingerprinting=False, manifest_path=False)
        self.gears.finders.register(ExtFinder([app_dir], ['.coffee', '.scss', '.handlebars']))

        self.gears.compilers.register('.scss', SCSSCompiler.as_handler())
        self.gears.compilers.register('.coffee', CoffeeScriptCompiler.as_handler())
        self.gears.compilers.register('.handlebars', CustomHandlebarsCompiler.as_handler())

        if env.is_prod():
            self.gears.compressors.register('application/javascript', UglifyJSCompressor.as_handler())
            self.gears.compressors.register('text/css', CleanCSSCompressor.as_handler())

        self.gears.register_defaults()


    def _public_assets(self, path):
        """
        Method is used by gears to determine what should be copied/published

        Allows only the app.js and app.css files to be compiled, filtering out
        all others since they should be included via require, require_tree,
        etc directives. Also, anything not js or css will be allowed through.

        :param path:
            The filesystem path to check

        :return:
            If the path should be copied to the public folder
        """

        if path in ['js/app.js', 'js/package.js', 'css/app.css']:
            return True
        return not any(path.endswith(ext) for ext in ('.css', '.js'))

    def compile(self):
        """
        Perform the cross-compile of the assets
        """

        self.gears.save()
