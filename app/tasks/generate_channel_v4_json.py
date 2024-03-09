import json
import os

from ..lib.json_datetime_encoder import JsonDatetimeEncoder
from ..lib.store_asset import store_asset
from ..models import package, library


if 'PACKAGE_CONTROL_ASSETS' not in os.environ:
    dirname = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.realpath(os.path.join(dirname, '..', '..', 'assets'))
else:
    assets_dir = os.environ['PACKAGE_CONTROL_ASSETS']

if not os.path.exists(assets_dir):
    raise Exception('The assets folder, "%s", does not exists. It can be ' +\
        'overridden by the environmental variable PACKAGE_CONTROL_ASSETS.')

output = {
    'schema_version': '4.0.0',
    'repositories': [],
    'packages_cache': {},
    'libraries_cache': {}
}

package_info = package.find.all(limit_one_per_package=True)
for name, info in package_info.items():
    repo = info['repository']
    del info['repository']
    del info['last_modified']

    if repo not in output['repositories']:
        output['repositories'].append(repo)

    if repo not in output['packages_cache']:
        output['packages_cache'][repo] = []

    output['packages_cache'][repo].append(info)

library_info = library.all(limit_one_per_library=True)
for name, info in library_info.items():
    repo = info['repository']
    del info['repository']

    if repo not in output['repositories']:
        output['repositories'].append(repo)

    if repo not in output['libraries_cache']:
        output['libraries_cache'][repo] = []

    output['libraries_cache'][repo].append(info)

output['repositories'] = sorted(output['repositories'])

store_asset(
    os.path.join(assets_dir, 'channel_v4.json'),
    json.dumps(
        output,
        cls=JsonDatetimeEncoder,
        check_circular=False,
        sort_keys=True
    )
)
