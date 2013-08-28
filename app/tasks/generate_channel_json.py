import re
import json
import os
import gzip
from urllib.parse import urlparse

from ..models import package
from ..lib.package_control.ca_certs import find_root_ca_cert
from ..lib.json_datetime_encoder import JsonDatetimeEncoder


if 'PACKAGE_CONTROL_ASSETS' not in os.environ:
    dirname = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.realpath(os.path.join(dirname, '..', '..', 'assets'))
else:
    assets_dir = os.environ['PACKAGE_CONTROL_ASSETS']

if not os.path.exists(assets_dir):
    raise Exception('The assets folder, "%s", does not exists. It can be ' +\
        'overridden by the environmental variable PACKAGE_CONTROL_ASSETS.')

certs_dir = os.path.join(assets_dir, 'certs')
if not os.path.exists(certs_dir):
    os.mkdir(certs_dir)

ssl_domains = ['api.github.com', 'api.bitbucket.org']

def add_ssl_domain(url):
    if not re.match('https://', url):
        return

    domain = urlparse(url).hostname
    if domain not in ssl_domains:
        ssl_domains.append(domain)

package_info = package.find.all()

output = {
    'schema_version': '2.0',
    'repositories': [],
    'packages_cache': {},
    'certs': {}
}

for name, info in package_info.items():
    repo = info['repository']
    del info['repository']
    del info['last_modified']

    add_ssl_domain(repo)

    if repo not in output['repositories']:
        output['repositories'].append(repo)

    if repo not in output['packages_cache']:
        output['packages_cache'][repo] = []

    output['packages_cache'][repo].append(info)

    for release in info['releases']:
        add_ssl_domain(release['url'])

for domain in ssl_domains:
    cert, cert_hash = find_root_ca_cert({}, domain)
    if not cert:
        print('Error fetching cert for %s' % domain)
        continue
    output['certs'][domain] = [
        cert_hash,
        "https://sublime.wbond.net/certs/" + cert_hash
    ]
    with open(os.path.join(certs_dir, cert_hash), 'w', encoding='utf-8') as f:
        f.write(cert)

output['repositories'] = sorted(output['repositories'])

new_json_path    = os.path.join(assets_dir, 'channel.json-new')
new_json_gz_path = os.path.join(assets_dir, 'channel.json.gz-new')
json_path        = os.path.join(assets_dir, 'channel.json')
json_gz_path     = os.path.join(assets_dir, 'channel.json.gz')

with open(new_json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, cls=JsonDatetimeEncoder)

os.rename(new_json_path, json_path)

with gzip.open(new_json_gz_path, 'w') as f:
    f.write(json.dumps(output, cls=JsonDatetimeEncoder).encode('utf-8'))

os.rename(new_json_gz_path, json_gz_path)
