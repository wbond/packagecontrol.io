import os
import re

from .. import config
from ..models import package, dependency
from .connection import connection
from .package_control.providers import REPOSITORY_PROVIDERS, CHANNEL_PROVIDERS


def mark():
    """
    Mark packages as removed that have a source that is no longer present in
    the channel, or that are no longer in one of the active sources
    """

    active_sources = find_active_sources()

    for info in package.find.old():
        # If there was an error trying to get information about a package,
        # which is indicated by the is_missing field, don't mark it as removed
        # because we want people to see that something is broken so that
        # someone fixes it.
        if info['is_missing']:
            continue

        # If none of the sources for a package is part of the channel,
        # we can deduce that the package was purposefully removed.
        if bool(set(info['sources']) & active_sources):
            continue

        package.modify.mark_removed(info['name'])
        print('Package "%s" marked as removed' % info['name'])

    for info in dependency.old():
        if info['is_missing']:
            continue

        if bool(set(info['sources']) & active_sources):
            continue

        dependency.mark_removed(info['name'])
        print('Dependency "%s" marked as removed' % info['name'])


def find_active_sources():
    """
    Find all sources that are currently used by the channel and the main
    repository.

    :return:
        A list of all active source URLs
    """

    settings = {}

    def resolve_path(path):
        dirname = os.path.dirname(os.path.abspath(__file__))
        dirname = os.path.join(dirname, path)
        return os.path.realpath(dirname)

    channel_settings = config.read('channel')

    channel = channel_settings['location']
    channel = resolve_path(channel)

    search = channel_settings.get('search', None)
    if search:
        search = resolve_path(search)
    replace = channel_settings.get('replace', None)

    for provider_cls in CHANNEL_PROVIDERS:
        if not provider_cls.match_url(channel):
            continue
        channel_provider = provider_cls(channel, settings)
        break

    # We also scan local repositories
    repositories_to_scan = []

    sources = set()
    for source in channel_provider.get_sources():
        if not re.match('^https?://', source):
            repositories_to_scan.append(source)
        source = source.replace(search, replace)
        sources.add(source)

    for repository in repositories_to_scan:
        for provider_cls in REPOSITORY_PROVIDERS:
            if not provider_cls.match_url(repository):
                continue

            repo_provider = provider_cls(repository, settings)
            for source in repo_provider.get_sources():
                source = source.replace(search, replace)
                sources.add(source)

            break

    return sources
