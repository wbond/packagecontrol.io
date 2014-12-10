import re
import os

from .package_control.providers import REPOSITORY_PROVIDERS, CHANNEL_PROVIDERS
from .. import config
from .connection import connection
from ..models import package, dependency



def mark():
    """
    Mark packages as removed that have a source that is no longer present in
    the channel, or that are no longer in one of the active sources
    """

    active_sources = find_active_sources()

    for info in package.find.old():
        mark_removed = False

        # If one of the sources for a package is no longer part of the channel,
        # we can deduce that the package was purposefully removed.
        for source in info['sources']:
            if source not in active_sources:
                mark_removed = True
                break

        # Packages that have not been seen in hours, but have no error indicates
        # that they were purposefully removed from a source that is still part
        # of the channel.
        if not info['is_missing']:
            mark_removed = True

        # The other possible situation is that there was an error trying to
        # get information about a package - which is indicated by the
        # is_missing field. We don't mark those as removed because we want
        # people to see that something is broken so that someone fixes it.

        if mark_removed:
            package.modify.mark_removed(info['name'])
            print('Package "%s" marked as removed' % info['name'])

    for info in dependency.old():
        mark_removed = False

        for source in info['sources']:
            if source not in active_sources:
                mark_removed = True
                break

        if not info['is_missing']:
            mark_removed = True

        if mark_removed:
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

    sources = {}
    for source in channel_provider.get_sources():
        if not re.match('^https?://', source):
            repositories_to_scan.append(source)
        source = source.replace(search, replace)
        sources[source] = True

    for repository in repositories_to_scan:
        for provider_cls in REPOSITORY_PROVIDERS:
            if not provider_cls.match_url(repository):
                continue

            repo_provider = provider_cls(repository, settings)
            for source in repo_provider.get_sources():
                source = source.replace(search, replace)
                sources[source] = True

            break

    return sources
