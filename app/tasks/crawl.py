import os
import subprocess
import sys

from ..models import package
from ..models import library
from ..lib.refresh_packages import refresh_packages


# Update the channel git repo
dirname = os.path.dirname(os.path.abspath(__file__))
dirname = os.path.join(dirname, '..', '..', 'channel')
dirname = os.path.realpath(dirname)

explicit_package = None
if len(sys.argv) > 1 and sys.argv[1]:
    explicit_package = sys.argv[1]

git_binary = None
for dir_ in os.environ['PATH'].split(os.pathsep):
    path = os.path.join(dir_, 'git')
    if os.path.exists(path):
        git_binary = path
        break

args = [git_binary, 'pull', 'origin', 'master']
proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, cwd=dirname)
output, _ = proc.communicate()
print(output.decode(encoding='utf-8'))


if explicit_package:
    valid_package_sources = package.sources.sources_for(explicit_package)
    valid_library_sources = []
else:
    valid_package_sources = package.sources.outdated_sources(60, 200)
    valid_library_sources = library.outdated_sources(60, 200)

invalid_package_sources = package.sources.invalid_sources(valid_package_sources)
invalid_library_sources = library.invalid_sources(valid_library_sources)

affected_packages, affected_libraries = refresh_packages(invalid_package_sources, invalid_library_sources)

print('AFFECTED PACKAGES')
print(affected_packages)
print('\nAFFECTED LIBRARIES')
print(affected_libraries)
