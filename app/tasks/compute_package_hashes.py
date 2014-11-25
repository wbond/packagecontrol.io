import hashlib
import os


root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
assets = os.path.join(root, 'assets')

for package in ['Package Control.sublime-package', 'bz2.sublime-package', 'ssl-linux.sublime-package', 'ssl-windows.sublime-package']:
    file_path = os.path.join(assets, package)
    with open(file_path, 'rb') as f:
        hash_ = hashlib.sha256(f.read()).hexdigest()
        print('%s: %s' % (package, hash_))
