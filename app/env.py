import os


version = None
name = 'dev'
if 'PACKAGE_CONTROL_ENV' in os.environ:
    name = os.environ['PACKAGE_CONTROL_ENV']


def reload():
    global version
    with open('./version.yml', 'r') as f:
        version = f.read().strip()
reload()


def is_dev():
    return name == 'dev'


def is_prod():
    return name == 'prod'
