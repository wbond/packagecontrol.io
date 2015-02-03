import hashlib
import os


root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
assets = os.path.join(root, 'assets')
ssl_dir = os.path.join(assets, 'ssl')


pc_path = os.path.join(assets, 'Package Control.sublime-package')
paths = [pc_path]
for (root, dirs, files) in os.walk(ssl_dir):
    for file in files:
        paths.append(os.path.join(ssl_dir, root, file))

for path in paths:
    with open(path, 'rb') as f:
        hash_ = hashlib.sha256(f.read()).hexdigest()
        filename = path.replace(assets + '/', '')
        print('%s: %s' % (filename, hash_))
