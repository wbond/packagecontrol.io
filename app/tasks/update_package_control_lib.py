import os
import re
import shutil
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
pc_path = os.path.join(root, 'app', 'lib', 'package_control')

src_path = os.path.expanduser('~/dev/Packages/Package Control/package_control')
if not os.path.exists(src_path):
    src_path = None

if len(sys.argv) > 1 and sys.argv[1]:
    src_path = os.path.abspath(os.path.expanduser(sys.argv[1]))

if not src_path or not os.path.exists(src_path):
    raise OSError('package_control source path not found')


REQUIRED_PATHS = [
    '__init__.py',
    'ca_certs.py',
    'cache.py',
    'clients',
    'cmd.py',
    'console_write.py',
    'deps',
    'download_manager.py',
    'downloaders',
    'file_not_found_error.py',
    'http',
    'open_compat.py',
    'providers',
    'semver.py',
    'text.py',
    'unicode.py',
    'versions.py',
]

PRESERVE_PATHS = [
    'http_cache.py',
    'readme.md',
    'show_error.py'
]

def ignore_dsstore_pyc(dir, items):
    out = []
    for i in items:
        if i == '.DS_Store':
            out.append(i)
        elif i == '__pycache__':
            out.append(i)
        elif i.endswith('.pyc'):
            out.append(i)
    return out

data = {}
for p in PRESERVE_PATHS:
    fp = os.path.join(pc_path, p)
    with open(fp, 'rb') as f:
        data[fp] = f.read()

shutil.rmtree(pc_path)
os.mkdir(pc_path)

for p in REQUIRED_PATHS:
    src_p = os.path.join(src_path, p)
    dst_p = os.path.join(pc_path, p)
    if os.path.isdir(src_p):
        shutil.copytree(src_p, dst_p, ignore=ignore_dsstore_pyc)
    else:
        shutil.copyfile(src_p, dst_p)

for fp in data:
    with open(fp, 'wb') as f:
        f.write(data[fp])
