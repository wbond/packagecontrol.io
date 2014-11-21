# Code to pull the latest python source code from Package Control
import os
import sys
import shutil

if sys.platform == 'darwin':
    source = '~/Library/Application Support/Sublime Text 3/Packages/Package Control/package_control/'
else:
    source = '~/.config/sublime-text-3/Packages/Package Control/package_control/'
source = os.path.expanduser(source)
script_dir = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
dest = os.path.realpath(os.path.join(script_dir, '../../app/lib/package_control/'))

files = [
    'clients/__init__.py',
    'clients/bitbucket_client.py',
    'clients/client_exception.py',
    'clients/github_client.py',
    'clients/json_api_client.py',
    'clients/readme_client.py',

    'downloaders/__init__.py',
    'downloaders/background_downloader.py',
    'downloaders/binary_not_found_error.py',
    'downloaders/caching_downloader.py',
    'downloaders/cli_downloader.py',
    'downloaders/curl_downloader.py',
    'downloaders/decoding_downloader.py',
    'downloaders/downloader_exception.py',
    'downloaders/http_error.py',
    'downloaders/limiting_downloader.py',
    'downloaders/non_clean_exit_error.py',
    'downloaders/non_http_error.py',
    'downloaders/rate_limit_exception.py',
    'downloaders/urllib_downloader.py',
    'downloaders/wget_downloader.py',
    'downloaders/win_downloader_exception.py',
    'downloaders/wininet_downloader.py',

    'http/__init__.py',
    'http/debuggable_http_connection.py',
    'http/debuggable_http_handler.py',
    'http/debuggable_http_response.py',
    'http/debuggable_https_response.py',
    'http/invalid_certificate_exception.py',
    'http/persistent_handler.py',
    'http/validating_https_connection.py',
    'http/validating_https_handler.py',
    'http/x509.py',

    'providers/__init__.py',
    'providers/bitbucket_repository_provider.py',
    'providers/channel_provider.py',
    'providers/github_repository_provider.py',
    'providers/github_user_provider.py',
    'providers/provider_exception.py',
    'providers/repository_provider.py',
    'providers/schema_compat.py',

    '__init__.py',
    'ca_certs.py',
    'cache.py',
    'cmd.py',
    'console_write.py',
    'download_manager.py',
    'file_not_found_error.py',
    # CUSTOM 'http_cache.py',
    'open_compat.py',
    '../readme.creole',
    'semver.py',
    # CUSTOM 'show_error.py',
    'unicode.py',
    'versions.py'
]

print('Source: %s' % source)
print('Destination: %s' % dest)
print('Copying:')

for file in files:
    source_file_path = os.path.join(source, file)
    dest_file_path = os.path.join(dest, file.replace('../', ''))
    print('  %s' % file)
    shutil.copyfile(source_file_path, dest_file_path)
