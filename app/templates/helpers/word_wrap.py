import re


def word_wrap(this, word):
    """
    Pybars helper for splitting long words with zero-width spaces
    """

    word = re.sub('([a-z])([0-9A-Z])', u"\\1\u200B\\2", word)
    word = re.sub('([0-9])([A-Z])', u"\\1\u200B\\2", word)
    word = word.replace('/', u"/\u200B")
    word = word.replace('.', u".\u200B")
    return word
