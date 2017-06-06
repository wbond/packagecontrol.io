import re
import tempfile
import os
import shutil
import zipfile
import pathlib
import subprocess
import json
from urllib.request import Request, urlopen
import base64
from urllib.error import URLError

from .package_control.providers import RepositoryProvider
from .package_control.download_manager import downloader, close_all_connections
from .package_control.downloaders.downloader_exception import DownloaderException
from .. import config
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
                return build_result(errors, warnings)

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


def run(cmd, path):
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=path
    )
    stdout, _ = proc.communicate()
    stdout = stdout.decode('utf-8').strip()
    returncode = proc.wait()
    return (returncode, stdout)


def package_name(data):
    if 'name' in data:
        return data['name']
    else:
        return os.path.basename(data['details'])


def test_pull_request(pr):
    """
    Test a pull request on https://github.com/wbond/package_control_channel
    """

    pr = int(pr)

    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        if not tmpdir:
            raise EnvironmentError('Unable to create tmpdir')

        code, res = run(['git', 'clone', 'https://github.com/wbond/package_control_channel.git'], tmpdir)
        if code != 0:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unable to clone https://github.com/wbond/package_control_channel'
            }

        channel_dir = os.path.join(tmpdir, 'package_control_channel')
        code, res = run(['git', 'fetch', '-q', 'origin', 'pull/%d/head:pr-%d' % (pr, pr)], channel_dir)
        if code != 0:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unable to fetch https://github.com/wbond/package_control_channel/pull/%d' % pr
            }

        code, res = run(['git', 'checkout', '-q', 'pr-%d' % pr], channel_dir)
        if code != 0:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unable to checkout https://github.com/wbond/package_control_channel/pull/%d' % pr
            }

        code, old_rev = run(['git', 'merge-base', 'master', 'pr-%d' % pr], channel_dir)
        if code != 0:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unable to find merge base for https://github.com/wbond/package_control_channel/pull/%d' % pr
            }

        filenames = []
        code, files_changed = run(['git', 'diff', '--name-status', old_rev], channel_dir)
        if code != 0:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unable to diff https://github.com/wbond/package_control_channel/pull/%d' % pr
            }

        for line in files_changed.splitlines():
            parts = re.split(r'\s+', line, 1)
            if len(parts) != 2:
                return {
                    '__status_code__': 500,
                    'result': 'error',
                    'message': 'git diff output included a line without status and filename\n\n%s' % files_changed
                }
            status, filename = parts
            if not filename.endswith('.json'):
                continue
            if not re.match(r'repository/(\w|0-9)\.json$', filename) and filename != 'channel.json':
                continue
            if status != 'M':
                return {
                    '__status_code__': 500,
                    'result': 'error',
                    'message': 'Unsure how to test a change that adds or removes a file, aborting'
                }
            filenames.append(filename)

        modified_pkgs = set()
        added_pkgs = set()
        removed_pkgs = set()

        added_pkg_data = {}

        added_repositories = set()
        removed_repositories = set()

        for filename in filenames:
            code, old_version = run(['git', 'show', '%s:%s' % (old_rev, filename)], channel_dir)
            code, new_version = run(['git', 'show', 'HEAD:%s' % filename], channel_dir)
            old_json = json.loads(old_version)
            new_json = json.loads(new_version)
            if filename == 'channel.json':
                removed_repositories = set(old_json['repositories']) - set(new_json['repositories'])
                added_repositories = set(new_json['repositories']) - set(old_json['repositories'])

            else:
                old_packages = [json.dumps(p) for p in old_json['packages']]
                new_packages = [json.dumps(p) for p in new_json['packages']]
                deleted = set(old_packages) - set(new_packages)
                added = set(new_packages) - set(old_packages)
                deleted_indexes = [old_packages.index(op) for op in deleted]
                added_indexes = [new_packages.index(np) for np in added]
                if len(deleted_indexes) == len(added_indexes):
                    for index in added_indexes:
                        modified_pkgs.add(package_name(new_json['packages'][index]))
                elif len(deleted_indexes) == 0:
                    for index in added_indexes:
                        pkg_name = package_name(new_json['packages'][index])
                        added_pkgs.add(pkg_name)
                        added_pkg_data[pkg_name] = new_json['packages'][index]
                else:
                    for index in deleted_indexes:
                        removed_pkgs.add(package_name(old_json['packages'][index]))

        output = []
        errors = False
        warnings = False

        settings = downloader_settings()

        if removed_repositories:
            output.append('Repositories removed:')
            for url in sorted(removed_repositories):
                output.append('  - %s' % url)

        if added_repositories:
            if output:
                output.append('')
            output.append('Repositories added:')
            for url in sorted(added_repositories):
                output.append('  - %s' % url)

        if added_repositories:
            for repo in added_repositories:
                if not repo.startswith('http://') and not repo.startswith('https://'):
                    continue

                output.append('')
                output.append('Processing repository "%s"' % repo)
                if repo.startswith('http://'):
                    errors = True
                    output.append('  - ERROR: External repositories added to the default channel must be served over HTTPS')
                    # Continue with testing regardless

                with downloader(repo, settings) as manager:
                    try:
                        raw_data = manager.fetch(repo, 'fetching repository')
                    except DownloaderException as e:
                        errors = True
                        output.append('  - ERROR: %s' % str(e))
                        continue

                try:
                    raw_data = raw_data.decode('utf-8')
                except UnicodeDecodeError:
                    errors = True
                    output.append('  - ERROR: Unable to decode JSON as UTF-8')
                    continue
                try:
                    repo_json = json.loads(raw_data)
                except ValueError:
                    errors = True
                    output.append('  - ERROR: Unable to parse JSON')
                    continue

                missing_key = False
                for key in ['schema_version', 'packages']:
                    if key not in repo_json:
                        missing_key = True
                        output.append('  - ERROR: Top-level key "%s" is missing' % key)
                        continue

                if missing_key:
                    errors = True
                    continue

                if repo_json['schema_version'] != '3.0.0':
                    errors = True
                    output.append('  - ERROR: "schema_version" must be "3.0.0"')
                    continue

                num_pkgs = 0
                for pkg_info in repo_json['packages']:
                    pkg_name = package_name(pkg_info)
                    added_pkgs.add(pkg_name)
                    added_pkg_data[pkg_name] = pkg_info
                    num_pkgs += 1
                output.append('  - Found %d package%s' % (num_pkgs, 's' if num_pkgs != 1 else ''))

        if removed_pkgs:
            if output:
                output.append('')
            output.append('Packages removed:')
            for name in sorted(removed_pkgs):
                output.append('  - %s' % name)

        if modified_pkgs:
            if output:
                output.append('')
            output.append('Packages modified:')
            for name in sorted(modified_pkgs):
                output.append('  - %s' % name)

        if added_pkgs:
            if output:
                output.append('')
            output.append('Packages added:')
            for name in sorted(added_pkgs):
                output.append('  - %s' % name)

        if added_pkgs:
            for name in sorted(added_pkgs):
                output.append('')
                output.append('Processing package "%s"' % name)
                data = added_pkg_data[name]
                test_results = run_tests(data)
                if test_results['result'] == 'success':
                    output.append('  - All checks passed')
                    continue
                if test_results['details']['errors']:
                    errors = True
                    for report in test_results['details']['errors']:
                        output.append('  - ERROR: %s' % report['message'])
                        for detail in report['details']:
                            output.append('    - %s' % detail)
                if test_results['details']['warnings']:
                    warnings = True
                    for report in test_results['details']['warnings']:
                        output.append('  - WARNING: %s' % report['message'])
                        for detail in report['details']:
                            output.append('    - %s' % detail)

        review_status = None
        if errors:
            event = 'REQUEST_CHANGES'
            review_status = 'ERROR'
        elif warnings:
            event = 'COMMENT'
            review_status = 'WARNING'
        else:
            event = 'APPROVE'
            review_status = 'SUCCESS'

        comment = [
            '### Automated testing result: %s' % review_status,
            '```',
        ]
        comment += output
        comment.append('```')
        payload = json.dumps({'body': '\n'.join(comment), 'event': event})

        github_pac = config.read_secret('github_personal_access_token')
        comment_url = 'https://api.github.com/repos/wbond/package_control_channel/pulls/%d/reviews' % pr

        auth_string = base64.encodestring(b'wbond:' + github_pac.encode('utf-8'))
        auth_header = 'Basic %s' % auth_string.decode('utf-8').strip()
        headers = {
            'Authorization': auth_header,
            'User-Agent': settings['user_agent'],
            'Content-Type': 'application/json',
        }

        try:
            req = Request(
                comment_url,
                data=payload.encode('utf-8'),
                headers=headers,
                method='POST'
            )
            res = urlopen(req)
            if res.getcode() != 200:
                return {
                    '__status_code__': 500,
                    'result': 'error',
                    'message': 'Error posting review to PR - %d' % res.getcode()
                }
        except URLError as e:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Error posting review to PR - %s' % str(e)
            }

        return {'result': 'completed', 'message': 'Checks ran successfully'}

    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
