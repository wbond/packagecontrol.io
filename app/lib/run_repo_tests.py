import re
import tempfile
import os
import shutil
import zipfile
import pathlib

from .package_control.providers import RepositoryProvider
from .package_control.download_manager import downloader, close_all_connections
from .package_control.downloaders.downloader_exception import DownloaderException
from .. import config
from . import st_package_reviewer
from .st_package_reviewer.check import file as file_checkers
from .st_package_reviewer.check.file.check_messages import CheckMessages
from .st_package_reviewer.check.file.check_resource_files import CheckHasSublimeSyntax


def downloader_settings():
    settings = config.read('crawler')
    if 'query_string_params' in settings and \
            'api.github.com' in settings['query_string_params']:
        settings['query_string_params']['api.github.com']['client_id'] = \
            config.read_secret('github_client_id')
        settings['query_string_params']['api.github.com']['client_secret'] = \
            config.read_secret('github_client_secret')
    settings['debug'] = False
    return settings


def build_result(errors, warnings):
    if errors:
        result = 'errors'
    elif warnings:
        result = 'warnings'
    else:
        result = 'success'
    return {'result': result, 'details': {'errors': errors, 'warnings': warnings}}


def format_report(report):
    if isinstance(report, str):
        return {'message': report, 'details': []}
    output = {'message': report.message, 'details': []}
    for elem in report.details:
        output['details'].append(elem)
    # We skip the exception backtrace so we don't expose env info
    return output


def run_tests(spec):
    """
    Runs repo tests for a repository

    :param spec:
        A dict of info for a single package, as loaded from a repository JSON file

    :return:

    """

    res, info = fetch_package_metadata(spec)
    if not res:
        return build_result([format_report(info)], [])

    tmpdir = None
    try:

        errors = []
        warnings = []

        if 'sublime' in info['name'].lower():
            errors.append('Package name contains the word "sublime"')

        if not info['releases']:
            if spec['releases']:
                errors.append(format_report('No releases found; check to ensure you have created a valid semver tag'))
            else:
                errors.append(format_report('No releases specified'))
        else:
            for release_source in spec['releases']:
                if 'branch' in release_source:
                    errors.append(format_report('Branch-based releases are not supported for new packages; please use "tags": true'))
                platforms = release_source.get('platforms', [])
                if set(platforms) == {'windows', 'osx', 'linux'} or platforms == ['*']:
                    warnings.append(format_report('The "platforms" key may be omitted instead of specifying all platform'))
        if info['readme'] is None:
            warnings.append(format_report('Creating a readme for your package will help users understand what it does and how to use it'))

        if not info['releases']:
            return build_result(errors, warnings)

        url = info['releases'][0]['url']
        settings = downloader_settings()
        name = info['name']

        tmpdir = tempfile.mkdtemp()
        if not tmpdir:
            return build_result([format_report('Could not create temp dir')], [])

        tmp_package_path = os.path.join(tmpdir, '%s.sublime-package' % name)
        tmp_package_dir = os.path.join(tmpdir, name)
        os.mkdir(tmp_package_dir)
        with open(tmp_package_path, 'wb') as package_file, downloader(url, settings) as manager:
            try:
                package_file.write(manager.fetch(url, 'fetching package'))
            except DownloaderException as e:
                errors.append(format_report(str(e)))
                return build_result(errors, warning)

        with zipfile.ZipFile(tmp_package_path, 'r') as package_zip:

            # Scan through the root level of the zip file to gather some info
            root_level_paths = []
            last_path = None
            for path in package_zip.namelist():
                if not isinstance(path, str):
                    path = path.decode('utf-8', 'strict')

                last_path = path

                if path.find('/') in [len(path) - 1, -1]:
                    root_level_paths.append(path)

            if last_path and len(root_level_paths) == 0:
                root_level_paths.append(last_path[0:last_path.find('/') + 1])

            # If there is only a single directory at the top level, the file
            # is most likely a zip from BitBucket or GitHub and we need
            # to skip the top-level dir when extracting
            skip_root_dir = len(root_level_paths) == 1 and \
                root_level_paths[0].endswith('/')

            for path in package_zip.namelist():
                dest = path
                if not isinstance(dest, str):
                    dest = dest.decode('utf-8', 'strict')

                # If there was only a single directory in the package, we remove
                # that folder name from the paths as we extract entries
                if skip_root_dir:
                    dest = dest[len(root_level_paths[0]):]

                dest = dest.replace('\\', '/')
                dest = os.path.join(tmp_package_dir, dest)

                if path.endswith('/'):
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                else:
                    dest_dir = os.path.dirname(dest)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    with open(dest, 'wb') as f:
                        f.write(package_zip.read(path))

            tmp_package_dir_pathlib = pathlib.Path(tmp_package_dir)
            for checker in file_checkers.get_checkers():
                checker_obj = checker(tmp_package_dir_pathlib)
                if checker == CheckMessages:
                    for release_source in spec['releases']:
                        if isinstance(release_source.get('tags'), str):
                            checker_obj.add_prefix(release_source.get('tags'))
                elif checker == CheckHasSublimeSyntax:
                    checker_obj.set_selector(info['releases'][0]['sublime_text'])

                checker_obj.perform_check()
                for failure in checker_obj.failures:
                    errors.append(format_report(failure))
                for warning in checker_obj.warnings:
                    warnings.append(format_report(warning))

        return build_result(errors, warnings)

    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


def fetch_package_metadata(spec):
    """
    Pull information about a package using the repository providers

    :param spec:
        A dict of info for a single package, as loaded from a repository JSON file

    :return:
        A two-element tuple, the first being True on success, or False on error.
        If successful, second element is a dict of info. If error, second element
        is a string error message.
    """

    settings = downloader_settings()

    def clean_message(exception):
        error = exception.args[0]
        for param, value in settings['query_string_params']['api.github.com'].items():
            regex = '[?&]' + re.escape(param) + '=' + re.escape(value)
            error = re.sub(regex, '', error)
        return error.replace(' in the repository https://example.com', '')

    provider = RepositoryProvider('https://example.com', settings)
    provider.schema_version = '3.0.0'
    provider.schema_major_version = 3
    provider.repo_info = {'schema_version': '3.0.0', 'packages': [spec], 'dependencies': []}

    try:
        for name, info in provider.get_packages():
            return (True, info)

        if provider.failed_sources:
            source, e = provider.failed_sources.popitem()
            return (False, clean_message(e))

        if provider.broken_packages:
            name, e = provider.broken_packages.popitem()
            return (False, clean_message(e))

    except (Exception) as e:
        return (False, clean_message(e))

    finally:
        close_all_connections()
