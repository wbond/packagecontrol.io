import os
import re
import importlib

import pybars

from . import env


# The pybars compiler used for compiling all partials and templates.
_compiler = pybars.Compiler()

# All of the helpers passed to templates when they are compiled.
# Format: {name: callable}
_helpers = {}

# All of the compiled partials and templates.
# Format: {name: callable}
_partials = {}
_templates = {}

# Static HTML content served up via Handlebars
_static = {}

# A list of when each partial and template was last compiled.
# Format: {path: {'mtime': float, 'reloader': callable}}
_reload_tracker = {}


static_root = os.path.join(os.path.dirname(__file__), 'html')
template_root = os.path.join(os.path.dirname(__file__), 'templates')
partials_root = os.path.join(template_root, 'partials')
helpers_root = os.path.join(template_root, 'helpers')


def _load_helper(path):
    """
    Loads/reloads a helper

    :param path:
        The absolute filesystem path to the helper
    """

    name = os.path.basename(path).replace('.py', '')
    module = importlib.import_module('app.templates.helpers.%s' % name)
    _helpers[name] = getattr(module, name)
    _reload_tracker[path] = {
        'mtime': os.stat(path).st_mtime,
        'reloader': _load_helper
    }


def load_helpers():
    """
    Loads up all of the helpers from the templates/helpers/ folder.
    """

    for filename in os.listdir(helpers_root):
        if filename[0] == '_':
            continue
        path = os.path.join(helpers_root, filename)
        _load_helper(path)


# Load all of the helpers into memory at boot
load_helpers()


def _load_partial(path):
    """
    Loads/reloads a partial

    :param path:
        The absolute filesystem path to the partial
    """

    name = os.path.basename(path).replace('.handlebars', '')
    with open(path, 'r', encoding='utf-8') as f:
        handlebars = f.read()
        # Compress whitespace if possible
        if re.search('<pre', handlebars, re.I) is None:
            handlebars = re.sub('[ \t\n]+', ' ', handlebars)
        _partials[name] = _compiler.compile(handlebars)
        _reload_tracker[path] = {
            'mtime': os.stat(path).st_mtime,
            'reloader': _load_partial
        }


def load_partials():
    """
    Loads up all of the partials from the templates/partials/ folder.
    """

    for filename in os.listdir(partials_root):
        if filename.find('.handlebars') == -1:
            continue
        path = os.path.join(partials_root, filename)
        _load_partial(path)


# Load all of the partial into memory at boot
load_partials()


# This is a gross hack on top of pybars to allow template to manipulate
# content that was printed before a given template expression
def _title_processor(output):
    new_output = ''.join(output)
    if new_output.find("{{title}}") != -1:
        title_tag_regex = re.compile("<title>(.*)</title>", re.S)
        title_handler_regex = re.compile("\{\{title\}\}(.*)\{\{/title\}\}", re.S)
        match = re.search(title_handler_regex, new_output)
        new_title = match.group(1)
        if new_title.find('Package Control') == -1:
            new_title += ' - Package Control'
        new_output = re.sub(title_handler_regex, '', new_output)
        new_output = re.sub(title_tag_regex, '<title>' + new_title + '</title>', new_output)
    return new_output


def _add_title_processor(func):
    def decorated(*args, **kwargs):
        return _title_processor(func(*args, **kwargs))
    return decorated


def _load_template(path):
    """
    Loads/reloads and compiles a template

    :param path:
        The absolute filesystem path to the template
    """

    # We inject the template into the app.handlebars so we can
    # better re-used the template for client-side templating also

    app_template_path = os.path.join(template_root, 'app.handlebars')
    app_handlebars = None
    with open(app_template_path, 'r', encoding='utf-8') as f:
        app_handlebars = f.read()

    name, ext = os.path.splitext(os.path.basename(path))
    with open(path, 'r', encoding='utf-8') as f:
        handlebars = f.read()
        # Compress whitespace if possible
        if re.search('<pre', handlebars, re.I) is None:
            handlebars = re.sub('[ \t\n]+', ' ', handlebars)
        if name == 'rss':
            _templates[name] = _compiler.compile(handlebars)
        else:
            handlebars = app_handlebars.replace('{{outlet}}', handlebars)
            _templates[name] = _add_title_processor(_compiler.compile(handlebars))
        _reload_tracker[path] = {
            'mtime': os.stat(path).st_mtime,
            'reloader': _load_template
        }


def _load_static(path):
    """
    Loads/reloads and static HTML file

    :param path:
        The absolute filesystem path to the file
    """

    name = path.replace(static_root + '/', '').replace('.html', '')
    with open(path, 'r', encoding='utf-8') as f:
        _static[name] = f.read().replace('<title>', '{{title}}').replace('</title>', '{{/title}}')
        _reload_tracker[path] = {
            'mtime': os.stat(path).st_mtime,
            'reloader': _load_static
        }


def static(name):
    """
    Renders an HTML file in a template, or just by itself

    :param name:
        The basename of the HTML file to render
    """

    if name not in _static:
        path = os.path.join(static_root, name + '.html')
        _load_static(path)

    return _static[name]


def template(name, data=None, **kwargs):
    """
    Merges data with a template from the templates/ folder.

    :param name:
        The name of the template in the templates/ folder. The
        .handlebars suffix will be automatically added.

    :param data:
        A dict of the data to pass to the template. Alternatively,
        any number of keyword args can be passed.

    :return:
        An HTML string
    """

    if data == None:
        data = kwargs

    # When running as dev, check the compilation time of
    # every template and partial and reload if necessary
    if env.is_dev():
        for path, info in _reload_tracker.items():
            if info['mtime'] < os.stat(path).st_mtime:
                info['reloader'](path)

    if name not in _templates:
        path = name + '.handlebars'
        path = os.path.join(template_root, path)
        _load_template(path)

    return _templates[name](data, helpers=_helpers, partials=_partials)
