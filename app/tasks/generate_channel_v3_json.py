import bz2
import gzip
import json
import os

from ..lib.json_datetime_encoder import JsonDatetimeEncoder
from ..models import package


if 'PACKAGE_CONTROL_ASSETS' not in os.environ:
    dirname = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.realpath(os.path.join(dirname, '..', '..', 'assets'))
else:
    assets_dir = os.environ['PACKAGE_CONTROL_ASSETS']

if not os.path.exists(assets_dir):
    raise Exception('The assets folder, "%s", does not exists. It can be ' +\
        'overridden by the environmental variable PACKAGE_CONTROL_ASSETS.')

output = {
    'schema_version': '3.0.0',
    'repositories': [],
    'packages_cache': {},
    'dependencies_cache': {}
}

package_info = package.find.all(limit_one_per_package=True, only_package_control=True)
for name, info in package_info.items():
    repo = info['repository']
    del info['repository']
    del info['last_modified']

    if repo not in output['repositories']:
        output['repositories'].append(repo)

    if repo not in output['packages_cache']:
        output['packages_cache'][repo] = []

    output['packages_cache'][repo].append(info)

output['repositories'] = sorted(output['repositories'])

new_json_path     = os.path.join(assets_dir, 'channel_v3.json-new')
new_json_gz_path  = os.path.join(assets_dir, 'channel_v3.json.gz-new')
new_json_bz2_path = os.path.join(assets_dir, 'channel_v3.json.bz2-new')
json_path         = os.path.join(assets_dir, 'channel_v3.json')
json_gz_path      = os.path.join(assets_dir, 'channel_v3.json.gz')
json_bz2_path     = os.path.join(assets_dir, 'channel_v3.json.bz2')

encoded_json = json.dumps(output, cls=JsonDatetimeEncoder).encode('utf-8')

with open(new_json_path, 'wb') as f:
    f.write(encoded_json)

os.rename(new_json_path, json_path)

with gzip.open(new_json_gz_path, 'w') as f:
    f.write(encoded_json)

os.rename(new_json_gz_path, json_gz_path)

with bz2.open(new_json_bz2_path, 'w') as f:
    f.write(encoded_json)

os.rename(new_json_bz2_path, json_bz2_path)
