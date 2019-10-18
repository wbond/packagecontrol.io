import os
import subprocess


sha1 = None
version = None
name = 'dev'
if 'PACKAGE_CONTROL_ENV' in os.environ:
    name = os.environ['PACKAGE_CONTROL_ENV']

def reload():
    global version
    global sha1
    with open('./version.yml', 'r') as f:
        version = f.read().strip()
    if os.path.exists('./git-sha1.yml'):
        with open('./git-sha1.yml', 'r') as f:
            sha1 = f.read().strip()
    else:
        sha1 = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
reload()


root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_dev():
    return name == 'dev'


def is_prod():
    return name == 'prod'
