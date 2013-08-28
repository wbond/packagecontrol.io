import re
import html

import pybars


def url_abbr(this, url, domain_only=False):
    """
    Pybars helper for generating the abbreviation of a URL
    """

    output = pybars.strlist()
    output.append('<a href="%s" title="%s">' % (html.escape(url), html.escape(url)))
    collapsableUrl = re.sub('^https?://(www\.)?', '', url)
    if domain_only:
        collapsableUrl = re.sub('/.*$', '', collapsableUrl)
    collapsableUrl = html.escape(collapsableUrl)
    collapsableUrl = collapsableUrl.replace('/', u"/\u200B")
    collapsableUrl = collapsableUrl.replace('.', u".\u200B")
    output.append(collapsableUrl)
    output.append('</a>')
    return output
