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
    'schema_version': '1.2',
    'repositories': [],
    'packages': {},
    'certs': {},
    'renamed_packages': {},
    # This stays empty since we have the proper name in the DB and will
    # always send the proper name via the "packages" key
    'package_name_map': {}
}

for name, info in package_info.items():
    repo = info['repository']
    del info['repository']
    del info['labels']
    del info['buy']
    del info['donate']
    del info['readme']
    del info['issues']

    add_ssl_domain(repo)
    for release in info['releases']:
        add_ssl_domain(release['url'])

    for prev_name in info['previous_names']:
        output['renamed_packages'][prev_name] = info['name']
    del info['previous_names']

    if repo not in output['repositories']:
        output['repositories'].append(repo)

    if repo not in output['packages']:
        output['packages'][repo] = []

    releases = info['releases']
    del info['releases']
    info['platforms'] = {}
    for release in releases:
        # Skip ST3-only packages
        if re.match('>=?3', release['sublime_text']):
            continue
        for platform in release['platforms']:
            if platform not in info['platforms']:
                info['platforms'][platform] = []
            info['platforms'][platform].append({
                'version': release['version'],
                'url': release['url']
            })

    output['packages'][repo].append(info)


for domain in ssl_domains:
    # Since I changed how I find SSL CA certs, the hashes changed, which leads
    # to a chicken and the egg situation, so here for legacy users I just
    # hard-code sublime.wbond.net to use the one they have in their settings
    if domain == 'sublime.wbond.net':
        output['certs']['sublime.wbond.net'] = [
            "7f4f8622b4fd001c7f648e09aae7edaa",
            "https://sublime.wbond.net/certs/7f4f8622b4fd001c7f648e09aae7edaa"
        ]
    else:
        print(domain)
        cert, cert_hash = find_root_ca_cert({}, domain)
        if not cert:
            print('Error fetching cert for %s' % domain)
            continue
        output['certs'][domain] = [
            cert_hash,
            "https://packagecontrol.io/certs/" + cert_hash
        ]
    with open(os.path.join(certs_dir, cert_hash), 'w', encoding='utf-8') as f:
        f.write(cert)

output['repositories'] = sorted(output['repositories'])

with open(os.path.join(assets_dir, 'repositories.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, cls=JsonDatetimeEncoder)

with gzip.open(os.path.join(assets_dir, 'repositories.json.gz'), 'w') as f:
    f.write(json.dumps(output, cls=JsonDatetimeEncoder).encode('utf-8'))
