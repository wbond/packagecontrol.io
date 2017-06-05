"""Parse JSON with C-style comments (and trailing commas).

Due to (multi-line) comments being stripped,
reported json.DecodeErrors may report "wrong" line and column numbers.
"""

import json
import re


__all__ = ('loads')

_re_js_comments_str = r"""
    (                               # Capture code
        (?:
            "(?:\\.|[^"\\])*"           # String literal
            |
            '(?:\\.|[^'\\])*'           # String literal
            |
            (?:[^/\n"']|/[^/*\n"'])+    # Any code besides newlines or string literals
            |
            \n                          # Newline
        )+                          # Repeat
    )|
    (/\* (?:[^*]|\*(?!/))* \*/)      # Multi-line comment
    |
    (?://(.*)$)                     # Comment
"""
_re_js_comments = re.compile(_re_js_comments_str, re.VERBOSE + re.MULTILINE)


def _strip_js_comments(string):
    """Strip C-style comments from a JSON file.

    Considers those encapsulated by strings.

    Original Source:
    http://stackoverflow.com/questions/2136363/matching-one-line-javascript-comments-with-re
    """
    parts = _re_js_comments.findall(string)
    # Stripping the whitespaces is, of course, optional, but the columns are fucked up anyway
    # with the comments being removed and it doesn't break things.
    return ''.join(x[0].strip(' ') for x in parts)


def _strip_trailing_json_commas(string):
    """Strip trailing commas in arrays and objects."""
    return re.sub(r",(\s*[\]}])", r"\1", string)


def _preprocess_json(string):
    return _strip_trailing_json_commas(_strip_js_comments(string))


def loads(string, *args, **kwargs):
    return json.loads(_preprocess_json(string), *args, **kwargs)
