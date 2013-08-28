import re

from lxml.html.clean import Cleaner, autolink_html


# Tags to allow through
_safe_tags = [
    'a',            'abbr',         'address',      'article',
    'aside',        'blockquote',   'br',           'button',
    'canvas',       'caption',      'cite',         'code',
    'col',          'colgroup',     'command',      'data',
    'datagrid',     'datalist',     'dd',           'del',
    'details',      'dfn',          'div',          'dl',
    'dt',           'em',           'fieldset',     'figcaption',
    'figure',       'footer',       'h1',           'h2',
    'h3',           'h4',           'h5',           'h6',
    'header',       'hgroup',       'hr',           'i',
    'img',          'input',        'ins',          'kbd',
    'label',        'legend',       'li',           'mark',
    'menu',         'meter',        'nav',          'ol',
    'optgroup',     'option',       'output',       'p',
    'pre',          'progress',     'q',            's',
    'samp',         'section',      'select',       'small',
    'span',         'strong',       'sub',          'summary',
    'sup',          'table',        'tbody',        'td',
    'textarea',     'tfoot',        'th',           'thead',
    'time',         'tr',           'u',            'ul',
    'var',          'wbr'
]

# Attributes to allow through
_safe_attrs = [
    'action',       'alt',          'cellpadding',  'cellspacing',
    'checked',      'cite',         'class',        'cols',
    'colspan',      'datetime',     'disabled',     'for',
    'headers',      'height',       'href',         'id',
    'label'         'lang',         'longdesc',     'maxlength',
    'multiple',     'name',         'readonly',     'rel',
    'rows',         'rowspan',      'scope',        'selected',
    'span',         'src',          'start',        'summary',
    'tabindex',     'target',       'title',        'type',
    'value',        'width'
]


def sanitize(html):
    if not html:
        return html
    cleaner = Cleaner(allow_tags=_safe_tags, safe_attrs_only=True, safe_attrs=_safe_attrs, remove_unknown_tags=False)
    html = autolink_html(cleaner.clean_html(html))

    parts = re.split('(<.*?>)', html)

    output = ''
    in_a_tag = False
    for part in parts:
        if not len(part):
            continue

        is_tag = part[0] == '<'
        if is_tag or in_a_tag:
            output += part
            if part[0:2].lower() == '<a':
                in_a_tag = True
            elif part[0:3].lower() == '</a':
                in_a_tag = False
            continue

        part = re.sub("([a-zA-Z0-9_\\-+\\.\']*[a-zA-Z0-9]@[0-9a-zA-Z\\-\\.]+\\.[a-zA-Z]{2,})", '<a href="mailto:\\1">\\1</a>', part)

        # After linking up emails, only look for twitter in the remaining parts
        sub_parts = re.split('(<.*?>)', part)
        part = ''
        for sub_part in sub_parts:
            part += re.sub("(?<![a-zA-Z0-9])@([0-9a-zA-Z_]{1,15})", '<a href="https://twitter.com/\\1">@\\1</a>', sub_part)

        output += part

    return output
