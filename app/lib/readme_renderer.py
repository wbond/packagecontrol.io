import re
import os

import textile
from creole import creole2html
from creole.rest2html.clean_writer import rest2html
import misaka
from misaka import HtmlRenderer, SmartyPants
from pygments import highlight, lexers, formatters
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from .sanitize import sanitize


_entities = [
    ['&', '&amp;'],
    ['<', '&lt;'],
    ['>', '&gt;'],
    ["'", '&apos;'],
    ['"', '&quot;']
]


def render(readme_info):
    """
    Turns a readme file into HTML

    :param readme_info:
        The dict from ReadmeClient, containing the keys:
          `format` - one of `markdown`, `textile`, `creole`, `rst`, `txt`
          `contents` - unicode/str contents of readme

    :return:
        An HTML string
    """

    contents = re.sub('\r\n', '\n', readme_info['contents'])

    if readme_info['format'] == 'markdown':
        contents = contents.replace("\t", '    ')
        output = _markdown(contents)

    elif readme_info['format'] == 'textile':
        output = textile.textile(contents, html_type='html')

    elif readme_info['format'] == 'creole':
        output = creole2html(contents)

    elif readme_info['format'] == 'rst':
        output = rest2html(contents, report_level=4)

    # Everything else is treated as txt
    else:
        output = contents
        for char, entity in _entities:
            output = output.replace(char, entity)
        output = output.replace('\n', '<br>\n')

    output = sanitize(output)

    if output.find('src=') != -1 or output.find('href=') != -1:
        url_dirname = os.path.dirname(readme_info['url']) + '/'
        output = re.sub('(<img\\s+[^>]*\\bsrc=["\'])(?!http://|https://|/)',
            '\\1' + url_dirname, output, 0, re.I)
        output = re.sub('(<a\\s+[^>]*\\bhref=["\'])(?!http://|https://|/)',
            '\\1' + url_dirname, output, 0, re.I)

    return output


class _HighlighterRenderer(HtmlRenderer, SmartyPants):
    def block_code(self, text, lang):
        s = ''
        if not lang:
            lang = 'text'
        lang = lang.lower()
        if lang == 'shell':
            lang = 'bash'
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except:
            s += '<div class="highlight"><span class="err">Error: language "%s" is not supported</span></div>' % lang
            lexer = get_lexer_by_name('text', stripall=True)
        formatter = HtmlFormatter()
        s += highlight(text, lexer, formatter)
        return s


def _markdown(text):
    render_flags = misaka.HTML_SKIP_STYLE
    renderer = _HighlighterRenderer(flags=render_flags)

    extensions = misaka.EXT_FENCED_CODE | misaka.EXT_NO_INTRA_EMPHASIS | \
        misaka.EXT_TABLES | misaka.EXT_AUTOLINK | misaka.EXT_STRIKETHROUGH | \
        misaka.EXT_SUPERSCRIPT
    md = misaka.Markdown(renderer, extensions=extensions)

    # Sundown seems not to properly handle multi-line HTML comments, and instead
    # turns the closing part of the tag into &ndash;>. To work around this, we
    # just strip HTML comments out.
    text = re.sub('<!--.*?-->', '', text, 0, re.S)

    # Pre-process the markdown to get fenced code block to render like GitHub
    # Unfortunately they no longer maintain sundown or redcarpet and have not
    # open-sourced their Markdown renderer, so this is a wild-goose chase.
    in_block = False
    last_line_blank = True
    lines = []
    for line in text.splitlines():
        if re.match('\s*(```|~~~)', line):
            if not in_block and not last_line_blank:
                line = "\n" + line
                in_block = True
            else:
                in_block = False
        lines.append(line)
        last_line_blank = re.match('^\s*$', line) != None

    return md.render("\n".join(lines))
