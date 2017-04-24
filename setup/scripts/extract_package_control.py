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

    'deps/__init__.py',
    'deps/asn1crypto/__init__.py',
    'deps/asn1crypto/_elliptic_curve.py',
    'deps/asn1crypto/_errors.py',
    'deps/asn1crypto/_ffi.py',
    'deps/asn1crypto/_inet.py',
    'deps/asn1crypto/_int.py',
    'deps/asn1crypto/_iri.py',
    'deps/asn1crypto/_ordereddict.py',
    'deps/asn1crypto/_teletex_codec.py',
    'deps/asn1crypto/_types.py',
    'deps/asn1crypto/algos.py',
    'deps/asn1crypto/core.py',
    'deps/asn1crypto/keys.py',
    'deps/asn1crypto/parser.py',
    'deps/asn1crypto/pem.py',
    'deps/asn1crypto/util.py',
    'deps/asn1crypto/version.py',
    'deps/asn1crypto/x509.py',
    'deps/oscrypto/_linux_bsd/__init__.py',
    'deps/oscrypto/_linux_bsd/trust_list.py',
    'deps/oscrypto/_osx/__init__.py',
    'deps/oscrypto/_osx/_core_foundation.py',
    'deps/oscrypto/_osx/_core_foundation_ctypes.py',
    'deps/oscrypto/_osx/_security.py',
    'deps/oscrypto/_osx/_security_ctypes.py',
    'deps/oscrypto/_osx/trust_list.py',
    'deps/oscrypto/_win/__init__.py',
    'deps/oscrypto/_win/_crypt32.py',
    'deps/oscrypto/_win/_crypt32_ctypes.py',
    'deps/oscrypto/_win/_decode.py',
    'deps/oscrypto/_win/_kernel32.py',
    'deps/oscrypto/_win/_kernel32_ctypes.py',
    'deps/oscrypto/_win/trust_list.py',
    'deps/oscrypto/__init__.py',
    'deps/oscrypto/_errors.py',
    'deps/oscrypto/_ffi.py',
    'deps/oscrypto/_types.py',
    'deps/oscrypto/errors.py',
    'deps/oscrypto/trust_list.py',
    'deps/oscrypto/version.py',

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
    '../readme.md',
    'semver.py',
    # CUSTOM 'show_error.py',
    'text.py',
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
    if not os.path.exists(os.path.dirname(dest_file_path)):
        os.makedirs(os.path.dirname(dest_file_path))
    shutil.copyfile(source_file_path, dest_file_path)
