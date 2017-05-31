import re

from .package_control.providers import RepositoryProvider
from .package_control.download_manager import close_all_connections
from .. import config


def fetch_package_metadata(spec):
    """
    Pull information about a package using the repository providers

    :param spec:
        A dict of info for a single package, as loaded from a repository JSON file

    :return:
        A dict of the resolved package info
    """

    settings = config.read('crawler')
    if 'query_string_params' in settings and \
            'api.github.com' in settings['query_string_params']:
        settings['query_string_params']['api.github.com']['client_id'] = \
            config.read_secret('github_client_id')
        settings['query_string_params']['api.github.com']['client_secret'] = \
            config.read_secret('github_client_secret')
    settings['debug'] = False

    def clean_message(exception):
        error = exception.args[0]
        for param, value in settings['query_string_params']['api.github.com'].items():
            regex = '[?&]' + re.escape(param) + '=' + re.escape(value)
            error = re.sub(regex, '', error)
        return error.replace('in the repository https://example.com', 'in the repository')

    provider = RepositoryProvider('https://example.com', settings)
    provider.schema_version = '3.0.0'
    provider.schema_major_version = 3
    provider.repo_info = {'schema_version': '3.0.0', 'packages': [spec], 'dependencies': []}

    try:
        for name, info in provider.get_packages():
            return {'result': 'success', 'info': info}

        if provider.failed_sources:
            source, e = provider.failed_sources.popitem()
            return {'result': 'error', 'message': clean_message(e)}

        if provider.broken_packages:
            name, e = provider.broken_packages.popitem()
            return {'result': 'error', 'message': '%s: %s' % (name, clean_message(e))}

    except (Exception) as e:
        return {'result': 'error', 'message': clean_message(e)}

    finally:
        close_all_connections()
