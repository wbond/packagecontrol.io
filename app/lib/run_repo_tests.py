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
import imp

from .package_control.providers import JsonRepositoryProvider
from .package_control.providers.schema_version import SchemaVersion
from .package_control.download_manager import close_all_connections, http_get
from .package_control.downloaders.downloader_exception import DownloaderException
from .. import config
from .st_package_reviewer.check import file as file_checkers
from .st_package_reviewer.check.file.check_messages import CheckMessages
from .st_package_reviewer.check.file.check_resource_files import CheckHasSublimeSyntax


# Hacks to get st_package_reviewer.check.file.ast working
for spr_mod in ('', '.check', '.check.file', '.check.file.ast'):
    full_spr_mod = 'st_package_reviewer' + spr_mod
    spr_mod_name = full_spr_mod.split('.')[-1]
    spr_mod_path = os.path.dirname(__file__)
    if spr_mod:
        spr_mod_path = os.path.join(
            spr_mod_path,
            *full_spr_mod.split('.')[:-1]
        )
    mod_info = imp.find_module(spr_mod_name, [spr_mod_path])
    imp.load_module(full_spr_mod, *mod_info)


def downloader_settings():
    settings = config.read('crawler')
    if 'http_basic_auth' in settings:
        auth = settings['http_basic_auth']
        if 'api.github.com' in auth:
            settings['http_basic_auth']['api.github.com'] = [
                auth['api.github.com'][0],
                config.read_secret('github_access_token_%s' % auth['api.github.com'][0])
            ]
        if 'gitlab.com' in auth:
            settings['http_basic_auth']['gitlab.com'] = [
                auth['gitlab.com'][0],
                config.read_secret('gitlab_access_token_%s' % auth['gitlab.com'][0])
            ]
        if 'api.bitbucket.org' in auth:
            settings['http_basic_auth']['api.bitbucket.org'] = [
                auth['api.bitbucket.org'][0],
                config.read_secret('bitbucket_app_password_%s' % auth['api.bitbucket.org'][0])
            ]
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

    name = info.get('name')
    if not isinstance(name, str) or '/' in name or '\\' in name:
        return build_result([format_report('Invalid package name')], [])

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

        if not isinstance(url, str) or not url.startswith('https://'):
            return build_result([format_report('Primary release URL does not begin with https://')], [])

        tmpdir = tempfile.mkdtemp()
        if not tmpdir:
            return build_result([format_report('Could not create temp dir')], [])

        tmp_package_path = os.path.join(tmpdir, '%s.sublime-package' % name)
        tmp_package_dir = os.path.join(tmpdir, name)
        os.mkdir(tmp_package_dir)
        with open(tmp_package_path, 'wb') as package_file:
            try:
                package_file.write(http_get(url, settings, 'fetching package'))
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
                path = path.replace('\\', '/')

                last_path = path

                if path.find('/') in [len(path) - 1, -1]:
                    root_level_paths.append(path)
                # Make sure there are no paths that look like security vulnerabilities
                if path[0] == '/' or '../' in path:
                    errors.append(format_report('The path "%s" appears to be attempting to access other parts of the filesystem' % path))
                    return build_result(errors, warnings)

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
                dest = dest.replace('\\', '/')

                # If there was only a single directory in the package, we remove
                # that folder name from the paths as we extract entries
                if skip_root_dir:
                    dest = dest[len(root_level_paths[0]):]

                dest = os.path.join(tmp_package_dir, dest)

                dest = os.path.abspath(dest)
                # Make sure there are no paths that look like security vulnerabilities
                if not dest.startswith(tmp_package_dir):
                    errors.append(format_report('The path "%s" appears to be attempting to access other parts of the filesystem' % path))
                    return build_result(errors, warnings)

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

    provider = JsonRepositoryProvider('https://example.com', settings)
    provider.schema_version = SchemaVersion('4.0.0')
    provider.repo_info = {'schema_version': '4.0.0', 'packages': [spec], 'libraries': []}

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


def github_api_request(settings, url, data=None):
    """
    Performs a request to the github api using urllib

    :param settings:
        A dict containing the key 'user_agent'

    :param url:
        The URL to request

    :param data:
        A dict of data to send as a POST - otherwise GET is used

    :return:
        A urllib.request.Response object
    """

    github_pac = config.read_secret('github_access_token_packagecontrol-bot')
    auth_string = base64.encodestring(b'packagecontrol-bot:' + github_pac.encode('utf-8'))
    auth_header = 'Basic %s' % auth_string.decode('utf-8').strip().replace('\n', '')
    headers = {
        'Authorization': auth_header,
        'User-Agent': settings['user_agent'],
    }
    method = 'GET'
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data).encode('utf-8')
        method = 'POST'
    req = Request(
        url,
        data=data,
        headers=headers,
        method=method
    )
    return urlopen(req)


def test_pull_request(pr):
    """
    Test a pull request on https://github.com/wbond/package_control_channel
    """

    pr = int(pr)
    settings = downloader_settings()

    pr_url = 'https://api.github.com/repos/wbond/package_control_channel/pulls/%d' % pr
    try:
        res = github_api_request(settings, pr_url)
        pr_details = json.loads(res.read().decode('utf-8'))
        if 'state' not in pr_details:
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'Unexpected format to PR details'
            }
        if pr_details['state'] != 'open':
            return {
                '__status_code__': 500,
                'result': 'error',
                'message': 'PR has already been closed'
            }
    except URLError as e:
        return {
            '__status_code__': 500,
            'result': 'error',
            'message': 'Error fetching PR details - %s' % str(e)
        }
    except UnicodeDecodeError:
        return {
            '__status_code__': 500,
            'result': 'error',
            'message': 'Error decoding PR details'
        }
    except ValueError:
        return {
            '__status_code__': 500,
            'result': 'error',
            'message': 'Error parsing PR details'
        }

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

        pkg_links = {}

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
                        if 'details' in added_pkg_data[pkg_name]:
                            pkg_links[pkg_name] = added_pkg_data[pkg_name]['details']
                else:
                    for index in deleted_indexes:
                        removed_pkgs.add(package_name(old_json['packages'][index]))

        output = []
        errors = False
        warnings = False

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

                try:
                    raw_data = http_get(repo, settings, 'fetching repository')
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

                if repo_json['schema_version'] not in('3.0.0', '4.0.0'):
                    errors = True
                    output.append('  - ERROR: "schema_version" must be "3.0.0" or "4.0.0"')
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
            '',
        ]
        if len(pkg_links):
            if len(pkg_links) == 1:
                name = list(pkg_links.keys())[0]
                comment.append('Repo link: [%s](%s)' % (name, pkg_links[name]))
            else:
                comment.append('Repo links:')
                comment.append('')
                for name in sorted(added_pkgs):
                    if name in pkg_links:
                        comment.append('  - [%s](%s)' % (name, pkg_links[name]))
                comment.append('')
        if errors or warnings:
            comment.append('[Results help](https://github.com/packagecontrol/st_package_reviewer/wiki/Package-checks)')
            comment.append('')
        comment.append('```')
        comment += output
        comment.append('```')

        comment_url = 'https://api.github.com/repos/wbond/package_control_channel/pulls/%d/reviews' % pr

        try:
            res = github_api_request(settings, comment_url, {'body': '\n'.join(comment), 'event': event})
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
