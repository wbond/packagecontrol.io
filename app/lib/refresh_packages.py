import re
import os
import sys
import traceback

from .package_control.providers import REPOSITORY_PROVIDERS, CHANNEL_PROVIDERS
from .package_control.download_manager import downloader, close_all_connections
from .package_control.clients.readme_client import ReadmeClient
from .. import config
from ..models import package
from .readme_renderer import render
from .readme_images import cache


def refresh_packages(invalid_sources=None):
    """
    Refresh the package information in the database

    :param invalid_sources:
        A list of source URLs to ignore

    :return:
        A list of the names of all of the packages that were refreshed
    """

    settings = config.read('crawler')
    if 'query_string_params' in settings and \
            'api.github.com' in settings['query_string_params']:
        settings['query_string_params']['api.github.com']['client_id'] = \
            config.read_secret('github_client_id')
        settings['query_string_params']['api.github.com']['client_secret'] = \
            config.read_secret('github_client_secret')

    def clean_url(exception):
        error = exception.args[0]
        for param, value in settings['query_string_params']['api.github.com'].items():
            regex = '[?&]' + re.escape(param) + '=' + re.escape(value)
            error = re.sub(regex, '', error)
            error = error.replace(search, replace)
        return error

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
    ignore = channel_settings.get('ignore', [])

    readme_client = ReadmeClient(settings)

    if invalid_sources:
        if search and replace:
            mapped_invalid_sources = []
            for source in invalid_sources:
                if source not in ignore:
                    source = source.replace(replace, search)
                mapped_invalid_sources.append(source)
            invalid_sources = mapped_invalid_sources

    for provider_cls in CHANNEL_PROVIDERS:
        if not provider_cls.match_url(channel):
            continue
        provider = provider_cls(channel, settings)
        repositories = provider.get_repositories()
        break

    affected_packages = []
    for repository in repositories:
        for provider_cls in REPOSITORY_PROVIDERS:
            if not provider_cls.match_url(repository):
                continue

            provider = provider_cls(repository, settings)
            for name, info in provider.get_packages(invalid_sources):
                try:
                    if search and replace:
                        mapped_sources = []
                        for source in info['sources']:
                            mapped_sources.append(source.replace(search, replace))
                        info['sources'] = mapped_sources

                    package.modify.mark_found(name)
                    package.modify.store(info)
                    affected_packages.append(name)

                    delete_readme = True
                    if info['readme']:
                        readme_info = readme_client.readme_info(info['readme'])
                        if readme_info:
                            readme_info['url'] = info['readme']
                            readme_info['rendered_html'] = render(readme_info)
                            readme_info['rendered_html'] = cache(settings, readme_info['rendered_html'])
                            readme_info['package'] = name
                            readme_info['source'] = readme_info['contents']
                            del readme_info['contents']
                            del readme_info['url']

                            delete_readme = False
                            package.modify.store_readme(readme_info)

                    if delete_readme:
                        package.modify.delete_readme(name)

                except (Exception) as e:
                    print('Exception processing package "%s":' % name, file=sys.stderr)
                    print('-' * 60, file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    print('-' * 60, file=sys.stderr)

            for source, exception in provider.get_failed_sources():
                package.modify.mark_missing(source, clean_url(exception))

            for package_name, exception in provider.get_broken_packages():
                package.modify.mark_missing_by_name(package_name, clean_url(exception))

            break

    close_all_connections()
    return affected_packages
